from abc import ABC, abstractmethod

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.schemas import AIAnswerResponse, AIAnswerRequest, AISource, SearchResult
from app.services.evaluation import check_answer_grounding
from app.services.search import search_chunks

SYSTEM_INSTRUCTIONS = (
    "You are an eDiscovery investigation assistant. Answer only from the supplied source excerpts. "
    "Use concise legal-review language. Include source citations exactly as provided. "
    "If the sources do not support an answer, say that the available documents do not establish it."
)


class AIProvider(ABC):
    name: str
    model: str | None
    enabled: bool

    @abstractmethod
    def generate_answer(self, question: str, sources: list[AISource]) -> str:
        raise NotImplementedError


class LocalGroundedProvider(AIProvider):
    name = "local"
    model = "extractive-grounded-v1"
    enabled = True

    def generate_answer(self, question: str, sources: list[AISource]) -> str:
        if not sources:
            return "The available documents do not establish an answer to this question."

        best_sources = sources[:3]
        evidence_sentences = []
        for source in best_sources:
            sentence = _first_sentence(source.snippet)
            evidence_sentences.append(f"{sentence} [{source.citation}]")
        return " ".join(evidence_sentences)


class ProviderDisabledFallback(AIProvider):
    name = "provider-disabled"
    model = None
    enabled = False

    def generate_answer(self, question: str, sources: list[AISource]) -> str:
        return LocalGroundedProvider().generate_answer(question, sources)


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        self.model = settings.ai_model
        self.enabled = bool(settings.ai_external_enabled and settings.openai_api_key)

    def generate_answer(self, question: str, sources: list[AISource]) -> str:
        if not self.enabled:
            return ProviderDisabledFallback().generate_answer(question, sources)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            prompt = build_grounded_prompt(question, sources)
            if hasattr(client, "responses"):
                response = client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                        {"role": "user", "content": prompt},
                    ],
                )
                return getattr(response, "output_text", "").strip() or ProviderDisabledFallback().generate_answer(
                    question, sources
                )

            completion = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                    {"role": "user", "content": prompt},
                ],
                temperature=0,
            )
            return completion.choices[0].message.content.strip()
        except Exception:
            return ProviderDisabledFallback().generate_answer(question, sources)


def answer_question(db: Session, request: AIAnswerRequest) -> AIAnswerResponse:
    search_results = search_chunks(db, request.question, matter_id=request.matter_id, limit=request.limit)
    sources = [_source_from_result(result) for result in search_results if result.citation]
    provider = _provider()
    answer = _ensure_citations(provider.generate_answer(request.question, sources), sources)
    citations = [source.citation for source in sources if source.citation in answer]
    grounding = check_answer_grounding(db, answer, citations)

    return AIAnswerResponse(
        question=request.question,
        answer=answer,
        provider=provider.name,
        model=provider.model,
        provider_enabled=provider.enabled,
        citations=citations,
        sources=sources,
        grounding=grounding,
    )


def build_grounded_prompt(question: str, sources: list[AISource]) -> str:
    source_text = "\n\n".join(
        f"Source {index}\nCitation: {source.citation}\nTitle: {source.title}\nExcerpt: {source.snippet}"
        for index, source in enumerate(sources, start=1)
    )
    return (
        f"Question: {question}\n\n"
        f"Sources:\n{source_text or 'No retrieved sources.'}\n\n"
        "Answer with only supported facts. Include citations in square brackets after each supported claim."
    )


def _provider() -> AIProvider:
    if settings.ai_provider.lower() == "openai":
        return OpenAIProvider()
    if settings.ai_external_enabled:
        return ProviderDisabledFallback()
    return LocalGroundedProvider()


def _source_from_result(result: SearchResult) -> AISource:
    return AISource(
        document_id=result.document_id,
        chunk_id=result.chunk_id,
        title=result.title,
        snippet=result.snippet,
        score=result.score,
        citation=result.citation or "",
    )


def _ensure_citations(answer: str, sources: list[AISource]) -> str:
    if not sources or any(source.citation in answer for source in sources):
        return answer
    return f"{answer} [{sources[0].citation}]"


def _first_sentence(text: str) -> str:
    clean_text = text.strip().strip(".")
    for delimiter in (". ", "? ", "! "):
        if delimiter in clean_text:
            return clean_text.split(delimiter, 1)[0].strip().strip(".")
    return clean_text
