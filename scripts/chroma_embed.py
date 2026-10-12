"""컷앤킵 Chroma 공용 글자 벡터.

임베딩 모델을 받지 않는다. 한글 2·3글자 조각을 256차원으로 해싱해
코사인 공간에 넣는다. 세 저장소(data, backend/data, Portfolio/ai/data)가
같은 함수 이름 `cutnkeep-char-ngram` 과 같은 차원을 써야 서로 읽을 수 있다.
"""

from __future__ import annotations

import math
import re
import zlib

DIM = 256
EMBEDDING_NAME = "cutnkeep-char-ngram"


def _grams(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", (text or "").lower())
    if len(compact) < 2:
        return [compact or "empty"]
    grams = [compact[i : i + 2] for i in range(len(compact) - 1)]
    if len(compact) >= 3:
        grams.extend(compact[i : i + 3] for i in range(len(compact) - 2))
    return grams


def embed_text(text: str) -> list[float]:
    """한 문장을 L2 정규화된 글자 벡터로 바꾼다."""
    vec = [0.0] * DIM
    for gram in _grams(text):
        vec[zlib.crc32(gram.encode("utf-8")) % DIM] += 1.0
    vec = [math.log1p(value) for value in vec]
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def cosine(left: str, right: str) -> float:
    a = embed_text(left)
    b = embed_text(right)
    return sum(x * y for x, y in zip(a, b))


_EMBEDDING = None


def embedding_function():
    """Chroma에 등록되는 임베딩 함수. chromadb 가 없으면 ImportError."""
    global _EMBEDDING
    if _EMBEDDING is not None:
        return _EMBEDDING

    import chromadb.utils.embedding_functions as ef_mod
    from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

    @ef_mod.register_embedding_function
    class CutnkeepCharNgramEmbedding(EmbeddingFunction[Documents]):
        @staticmethod
        def name() -> str:
            return EMBEDDING_NAME

        def __call__(self, input: Documents) -> Embeddings:
            return [embed_text(text) for text in input]

        @staticmethod
        def build_from_config(config: dict) -> "CutnkeepCharNgramEmbedding":
            return CutnkeepCharNgramEmbedding()

        def get_config(self) -> dict:
            return {"dim": DIM}

    _EMBEDDING = CutnkeepCharNgramEmbedding()
    return _EMBEDDING
