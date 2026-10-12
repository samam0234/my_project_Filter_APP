"""문장 해석용 Chroma 글자 벡터.

임베딩 모델은 받지 않는다. 루트 scripts/chroma_embed.py 와 이름·차원이 같아야
data/chroma 의 verified_feedback 을 그대로 읽을 수 있다.
"""

from __future__ import annotations

import math
import re
import zlib

DIM = 256
EMBEDDING_NAME = "cutnkeep-char-ngram"
_EMBEDDING = None


def _grams(text: str) -> list[str]:
    compact = re.sub(r"\s+", "", (text or "").lower())
    if len(compact) < 2:
        return [compact or "empty"]
    grams = [compact[i : i + 2] for i in range(len(compact) - 1)]
    if len(compact) >= 3:
        grams.extend(compact[i : i + 3] for i in range(len(compact) - 2))
    return grams


def embed_text(text: str) -> list[float]:
    vec = [0.0] * DIM
    for gram in _grams(text):
        vec[zlib.crc32(gram.encode("utf-8")) % DIM] += 1.0
    vec = [math.log1p(value) for value in vec]
    norm = math.sqrt(sum(value * value for value in vec)) or 1.0
    return [value / norm for value in vec]


def embedding_function():
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
