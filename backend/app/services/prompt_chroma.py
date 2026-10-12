"""승인 문장 Chroma.

backend/data/chroma 의 approved_prompts 는 지금 색인한 승인 예시다.
루트 data/chroma 의 verified_feedback 은 파일로 남은 교정·좋아요다.
둘 다 없으면 글자 n-gram 결과만 쓴다. 저장소를 열지 못해도 해석은 계속한다.
"""

from __future__ import annotations

import hashlib
import threading
from pathlib import Path

from loguru import logger

from app.services.chroma_embed import embedding_function
from app.services.prompt_rag import Example, Hit

APPROVED = "approved_prompts"
VERIFIED = "verified_feedback"
_LOCK = threading.Lock()
_CLIENTS: dict[str, object] = {}


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _row_id(prompt: str) -> str:
    return hashlib.sha1(_normalize(prompt).encode("utf-8")).hexdigest()


def _client(path: Path):
    import chromadb
    from chromadb.config import Settings

    path.mkdir(parents=True, exist_ok=True)
    key = str(path.resolve())
    with _LOCK:
        client = _CLIENTS.get(key)
        if client is None:
            client = chromadb.PersistentClient(path=key, settings=Settings(anonymized_telemetry=False))
            _CLIENTS[key] = client
        return client


def _collection(path: Path, name: str):
    return _client(path).get_or_create_collection(
        name=name,
        embedding_function=embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def sync_examples(store: Path, examples: list[Example], collection_name: str = APPROVED) -> None:
    """예시 목록으로 컬렉션을 맞춘다. 없어진 문장은 뺀다."""
    rows = [
        {"prompt": ex.prompt.strip(), "answer": ex.answer[:2000], "source": ex.source}
        for ex in examples
        if ex.prompt.strip() and ex.answer
    ]
    collection = _collection(store, collection_name)
    ids = [_row_id(row["prompt"]) for row in rows]
    keep = set(ids)
    existing = collection.get(include=[])
    stale = [item for item in existing.get("ids", []) if item not in keep]
    if stale:
        collection.delete(ids=stale)
    if rows:
        collection.upsert(
            ids=ids,
            documents=[row["prompt"] for row in rows],
            metadatas=[{"answer": row["answer"], "source": row["source"]} for row in rows],
        )


def search_store(
    store: Path,
    query: str,
    collection_name: str,
    k: int = 3,
    min_similarity: float = 0.55,
) -> list[Hit]:
    query = (query or "").strip()
    if not query or k <= 0 or not store.exists():
        return []
    collection = _collection(store, collection_name)
    count = collection.count()
    if count <= 0:
        return []
    raw = collection.query(
        query_texts=[query],
        n_results=min(k, count),
        include=["documents", "metadatas", "distances"],
    )
    documents = (raw.get("documents") or [[]])[0]
    metadatas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]
    hits: list[Hit] = []
    for document, meta, distance in zip(documents, metadatas, distances):
        if not document or not isinstance(meta, dict):
            continue
        similarity = 1.0 - float(distance)
        answer = str(meta.get("answer") or "")
        source = str(meta.get("source") or "")
        if similarity < min_similarity or not answer or not source:
            continue
        hits.append(Hit(Example(document, answer, source), round(similarity, 4)))
    hits.sort(key=lambda hit: hit.score, reverse=True)
    return hits[:k]


def search_grounding(runtime: Path, shared: Path, query: str, k: int, min_similarity: float) -> list[Hit]:
    """두 저장소를 읽고, 같은 문장은 높은 점수만 남긴다."""
    found: dict[str, Hit] = {}
    stores = ((runtime, APPROVED), (shared, VERIFIED))
    for path, name in stores:
        try:
            hits = search_store(path, query, name, k=k, min_similarity=min_similarity)
        except Exception as exc:
            logger.warning("프롬프트 Chroma 검색 실패 ({} {}): {}", path, name, exc)
            continue
        for hit in hits:
            key = _normalize(hit.example.prompt)
            current = found.get(key)
            if current is None or hit.score > current.score:
                found[key] = hit
    ranked = sorted(found.values(), key=lambda hit: hit.score, reverse=True)
    return ranked[:k]


def merge_hits(lexical: list[Hit], vector: list[Hit], k: int) -> list[Hit]:
    """글자 검색을 유지하고, 아직 없는 확인 문장이 있으면 한 자리를 그 예시에 쓴다."""
    if k <= 0:
        return []
    seen = {_normalize(hit.example.prompt) for hit in lexical}
    extra = next((hit for hit in vector if _normalize(hit.example.prompt) not in seen), None)
    if extra is None:
        return lexical[:k]
    if not lexical:
        return [extra]
    kept = list(lexical[: max(0, k - 1)])
    kept.append(extra)
    return kept[:k]
