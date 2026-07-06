from abc import ABC, abstractmethod
from dataclasses import dataclass
import re

from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.matter import Matter
from app.models.schemas import AIAnswerResponse, AIAnswerRequest, AISource, SearchResult
from app.services.evaluation import check_answer_grounding, persist_answer_evaluation
from app.services.search import search_chunks

SYSTEM_INSTRUCTIONS = (
    "You are an eDiscovery investigation assistant. Answer only from the supplied source excerpts. "
    "Use concise legal-review language. Include source citations exactly as provided. "
    "If the sources do not support an answer, say that the available documents do not establish it."
)
NO_ANSWER_TEXT = "The available documents do not establish an answer to this question."
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']*")
EMAIL_PATTERN = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")
PHONE_PATTERN = re.compile(r"\b(?:\+?1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}\b")
SSN_PATTERN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
CURRENCY_PATTERN = re.compile(r"\$\d[\d,]*(?:\.\d{2})?")
ANSWER_MODES = {"summary", "chronology", "issues", "contradiction", "privilege", "deposition"}
LOCAL_STOPWORDS = {
    "about",
    "after",
    "answer",
    "before",
    "does",
    "document",
    "documents",
    "did",
    "for",
    "from",
    "have",
    "anyone",
    "that",
    "the",
    "this",
    "what",
    "when",
    "where",
    "which",
    "with",
}


@dataclass(frozen=True)
class RedactionResult:
    text: str
    count: int


class AIProvider(ABC):
    name: str
    model: str | None
    enabled: bool

    @abstractmethod
    def generate_answer(self, question: str, sources: list[AISource], answer_mode: str = "summary") -> str:
        raise NotImplementedError


class LocalGroundedProvider(AIProvider):
    name = "local"
    model = "extractive-grounded-v1"
    enabled = True

    def generate_answer(self, question: str, sources: list[AISource], answer_mode: str = "summary") -> str:
        if not sources:
            return NO_ANSWER_TEXT

        question_terms = _important_question_terms(question)
        if question_terms and not any(_source_overlap(source, question_terms) >= _minimum_overlap(question_terms) for source in sources):
            return NO_ANSWER_TEXT

        evidence_sentences = []
        used_citations = set()
        ranked_sources = sorted(
            sources,
            key=lambda source: (_source_overlap(source, question_terms), source.score),
            reverse=True,
        )
        for source in ranked_sources:
            if source.citation in used_citations:
                continue
            sentence = _best_sentence(source.snippet, question_terms)
            if not sentence:
                continue
            evidence_sentences.append(f"{sentence} [{source.citation}]")
            used_citations.add(source.citation)
            if len(evidence_sentences) >= 3:
                break
        if not evidence_sentences:
            return NO_ANSWER_TEXT
        return _format_answer_for_mode(answer_mode, evidence_sentences)


class ProviderDisabledFallback(AIProvider):
    name = "provider-disabled"
    model = None
    enabled = False

    def generate_answer(self, question: str, sources: list[AISource], answer_mode: str = "summary") -> str:
        return LocalGroundedProvider().generate_answer(question, sources, answer_mode)


class OpenAIProvider(AIProvider):
    name = "openai"

    def __init__(self) -> None:
        self.model = settings.ai_model
        self.enabled = bool(settings.ai_external_enabled and settings.openai_api_key)

    def generate_answer(self, question: str, sources: list[AISource], answer_mode: str = "summary") -> str:
        if not self.enabled:
            return ProviderDisabledFallback().generate_answer(question, sources, answer_mode)

        try:
            from openai import OpenAI

            client = OpenAI(api_key=settings.openai_api_key)
            prompt = build_grounded_prompt(question, sources, answer_mode)
            if hasattr(client, "responses"):
                response = client.responses.create(
                    model=self.model,
                    input=[
                        {"role": "system", "content": SYSTEM_INSTRUCTIONS},
                        {"role": "user", "content": prompt},
                    ],
                )
                return getattr(response, "output_text", "").strip() or ProviderDisabledFallback().generate_answer(
                    question, sources, answer_mode
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
            return ProviderDisabledFallback().generate_answer(question, sources, answer_mode)


def answer_question(
    db: Session,
    request: AIAnswerRequest,
    matter_ids: list[int] | None = None,
) -> AIAnswerResponse:
    policy = _matter_ai_policy(db, request.matter_id)
    search_results = search_chunks(
        db,
        request.question,
        matter_id=request.matter_id,
        matter_ids=matter_ids,
        limit=request.limit,
    )
    sources = [_source_from_result(result) for result in search_results if result.citation]
    answer_mode = _allowed_answer_mode(request.answer_mode, policy)
    redacted_question = request.question
    redacted_sources = sources
    redaction_count = 0
    provider = _provider(policy)
    if provider.name != "local" and request.apply_redactions and policy["redaction_required"]:
        redacted_question_result = redact_for_external_provider(request.question)
        redacted_question = redacted_question_result.text
        redacted_sources, source_redaction_count = _redacted_sources(sources)
        redaction_count = redacted_question_result.count + source_redaction_count
    answer = _ensure_citations(provider.generate_answer(redacted_question, redacted_sources, answer_mode), sources)
    citations = [source.citation for source in sources if source.citation in answer]
    grounding = check_answer_grounding(db, answer, citations)
    persist_answer_evaluation(
        db,
        matter_id=request.matter_id,
        question=request.question,
        answer=answer,
        citations=citations,
        dataset_name="live_ai_answers",
        case_id=f"mode-{answer_mode}",
    )

    return AIAnswerResponse(
        question=request.question,
        answer=answer,
        answer_mode=answer_mode,
        provider=provider.name,
        model=provider.model,
        provider_enabled=provider.enabled,
        redactions_applied=redaction_count > 0,
        redaction_count=redaction_count,
        policy=policy,
        citations=citations,
        sources=sources,
        grounding=grounding,
    )


def build_grounded_prompt(question: str, sources: list[AISource], answer_mode: str = "summary") -> str:
    source_text = "\n\n".join(
        f"Source {index}\nCitation: {source.citation}\nTitle: {source.title}\nExcerpt: {source.snippet}"
        for index, source in enumerate(sources, start=1)
    )
    return (
        f"Question: {question}\n\n"
        f"Answer mode: {answer_mode}\n\n"
        f"Sources:\n{source_text or 'No retrieved sources.'}\n\n"
        "Answer with only supported facts. Include citations in square brackets after each supported claim. "
        "For chronology mode, order dated events. For issues mode, group by legal issue. "
        "For contradiction mode, identify tensions or say none are established. "
        "For privilege mode, flag privilege-risk signals without making a final privilege call. "
        "For deposition mode, provide concise question topics grounded in cited evidence."
    )


def redact_for_external_provider(text: str) -> RedactionResult:
    count = 0
    redacted = text
    for pattern, replacement in (
        (EMAIL_PATTERN, "[REDACTED_EMAIL]"),
        (SSN_PATTERN, "[REDACTED_SSN]"),
        (PHONE_PATTERN, "[REDACTED_PHONE]"),
        (CURRENCY_PATTERN, "[REDACTED_AMOUNT]"),
    ):
        redacted, substitutions = pattern.subn(replacement, redacted)
        count += substitutions
    return RedactionResult(text=redacted, count=count)


def _provider(policy: dict) -> AIProvider:
    if settings.ai_provider.lower() == "openai" and not policy["external_allowed"]:
        return LocalGroundedProvider()
    if settings.ai_provider.lower() == "openai":
        return OpenAIProvider()
    if settings.ai_external_enabled:
        return ProviderDisabledFallback()
    return LocalGroundedProvider()


def _matter_ai_policy(db: Session, matter_id: int | None) -> dict:
    default_modes = sorted(ANSWER_MODES)
    if matter_id is None:
        return {
            "external_allowed": False,
            "redaction_required": True,
            "allowed_modes": default_modes,
            "policy_source": "default_no_matter",
        }
    matter = db.get(Matter, matter_id)
    if matter is None:
        return {
            "external_allowed": False,
            "redaction_required": True,
            "allowed_modes": default_modes,
            "policy_source": "missing_matter",
        }
    allowed_modes = _parse_allowed_modes(matter.ai_allowed_modes) or default_modes
    return {
        "external_allowed": bool(matter.ai_external_allowed),
        "redaction_required": bool(matter.ai_redaction_required),
        "allowed_modes": allowed_modes,
        "policy_source": "matter",
    }


def _parse_allowed_modes(raw_modes: str | None) -> list[str]:
    if not raw_modes:
        return []
    try:
        import json

        parsed = json.loads(raw_modes)
    except json.JSONDecodeError:
        return []
    if not isinstance(parsed, list):
        return []
    return [mode for mode in parsed if isinstance(mode, str) and mode in ANSWER_MODES]


def _allowed_answer_mode(answer_mode: str, policy: dict) -> str:
    allowed_modes = set(policy.get("allowed_modes") or ANSWER_MODES)
    return answer_mode if answer_mode in allowed_modes else "summary"


def _redacted_sources(sources: list[AISource]) -> tuple[list[AISource], int]:
    redacted_sources = []
    redaction_count = 0
    for source in sources:
        result = redact_for_external_provider(source.snippet)
        redaction_count += result.count
        redacted_sources.append(source.model_copy(update={"snippet": result.text}))
    return redacted_sources, redaction_count


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
    if answer == NO_ANSWER_TEXT:
        return answer
    if not sources or any(source.citation in answer for source in sources):
        return answer
    return f"{answer} [{sources[0].citation}]"


def _format_answer_for_mode(answer_mode: str, evidence_sentences: list[str]) -> str:
    if answer_mode == "chronology":
        return "\n".join(f"{index}. {sentence}" for index, sentence in enumerate(evidence_sentences, start=1))
    if answer_mode == "issues":
        return "\n".join(f"- Issue {index}: {sentence}" for index, sentence in enumerate(evidence_sentences, start=1))
    if answer_mode == "contradiction":
        return "Potential contradiction check:\n" + "\n".join(
            f"- Evidence {index}: {sentence}" for index, sentence in enumerate(evidence_sentences, start=1)
        )
    if answer_mode == "privilege":
        return "Privilege risk review:\n" + "\n".join(
            f"- Signal {index}: {sentence}" for index, sentence in enumerate(evidence_sentences, start=1)
        )
    if answer_mode == "deposition":
        return "Deposition preparation topics:\n" + "\n".join(
            f"- Topic {index}: Ask about {sentence}" for index, sentence in enumerate(evidence_sentences, start=1)
        )
    return " ".join(evidence_sentences)


def _important_question_terms(question: str) -> set[str]:
    return {
        token.lower()
        for token in TOKEN_PATTERN.findall(question)
        if len(token) >= 3 and token.lower() not in LOCAL_STOPWORDS
    }


def _source_overlap(source: AISource, question_terms: set[str]) -> int:
    if not question_terms:
        return 1
    source_terms = {token.lower() for token in TOKEN_PATTERN.findall(f"{source.title} {source.snippet}")}
    return len(question_terms & source_terms)


def _minimum_overlap(question_terms: set[str]) -> int:
    if len(question_terms) <= 2:
        return 1
    return 2


def _best_sentence(text: str, question_terms: set[str]) -> str:
    clean_text = text.strip().strip(".")
    sentences = [sentence.strip().strip(".") for sentence in re.split(r"(?<=[.!?])\s+", clean_text) if sentence.strip()]
    if not sentences:
        return clean_text
    if not question_terms:
        return sentences[0]
    scored = []
    for sentence in sentences:
        sentence_terms = {token.lower() for token in TOKEN_PATTERN.findall(sentence)}
        scored.append((len(question_terms & sentence_terms), len(sentence_terms), sentence))
    scored.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return scored[0][2]
