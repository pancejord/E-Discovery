from dataclasses import dataclass
from hashlib import sha256


@dataclass(frozen=True)
class TextChunk:
    chunk_index: int
    text: str
    text_hash: str
    char_start: int
    char_end: int
    token_count: int


def chunk_text(text: str, max_chars: int = 1200, overlap_chars: int = 200) -> list[TextChunk]:
    normalized = " ".join(text.split())
    if not normalized:
        return []

    chunks: list[TextChunk] = []
    start = 0
    while start < len(normalized):
        end = min(start + max_chars, len(normalized))
        if end < len(normalized):
            boundary = normalized.rfind(" ", start, end)
            if boundary > start + max_chars // 2:
                end = boundary

        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(
                TextChunk(
                    chunk_index=len(chunks),
                    text=chunk,
                    text_hash=sha256(chunk.encode("utf-8")).hexdigest(),
                    char_start=start,
                    char_end=end,
                    token_count=len(chunk.split()),
                )
            )

        if end >= len(normalized):
            break
        start = max(end - overlap_chars, start + 1)

    return chunks
