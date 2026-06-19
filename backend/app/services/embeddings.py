import math
import re
from hashlib import blake2b

from app.core.config import settings

EMBEDDING_MODEL = "local-hash-v1"
TOKEN_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9_\-']*")


def embed_text(text: str) -> list[float]:
    vector = [0.0] * settings.embedding_dimension
    for token in TOKEN_PATTERN.findall(text.lower()):
        digest = blake2b(token.encode("utf-8"), digest_size=8).digest()
        bucket = int.from_bytes(digest[:4], "big") % settings.embedding_dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[bucket] += sign

    magnitude = math.sqrt(sum(value * value for value in vector))
    if magnitude == 0:
        return vector
    return [value / magnitude for value in vector]


def cosine_similarity(left: list[float] | None, right: list[float] | None) -> float:
    if not left or not right:
        return 0.0
    return sum(a * b for a, b in zip(left, right))
