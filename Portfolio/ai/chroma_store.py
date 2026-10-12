"""안내 문서와 배운 질문을 Portfolio/ai/data/chroma 에 둔다.

화면의 대화 목록은 브라우저 localStorage다. 이 저장소는 검색 보조용이다.
임베딩 모델은 받지 않는다. 열지 못하면 호출한 쪽이 기존 BM25만 쓴다.
"""

from __future__ import annotations

import hashlib
import os
import threading
from pathlib import Path

from chroma_embed import embedding_function

DOCS = "guide_docs"
MEMORY = "guide_memory"
_LOCK = threading.Lock()
_CLIENTS: dict[str, object] = {}


def store_path() -> Path:
    override = os.environ.get("PORTFOLIO_CHROMA_DIR")
    if override:
        return Path(override)
    return Path(__file__).resolve().parent / "data" / "chroma"


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


def _collection(name: str):
    return _client(store_path()).get_or_create_collection(
        name=name,
        embedding_function=embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def _doc_id(source: str, title: str, part: int) -> str:
    raw = f"{source}|{title}|{part}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()


def _signature(docs) -> str:
    rows: list[str] = []
    seen: set[str] = set()
    for doc in docs:
        meta = getattr(doc, "metadata", {}) or {}
        path = str(meta.get("path") or meta.get("source") or "")
        if not path or path in seen:
            continue
        seen.add(path)
        try:
            stamp = Path(path).stat().st_mtime_ns
        except OSError:
            stamp = len(getattr(doc, "page_content", "") or "")
        rows.append(f"{path}:{stamp}")
    return hashlib.sha1("\n".join(rows).encode("utf-8")).hexdigest()


def ensure_documents(docs) -> int:
    """문서 조각이 바뀌었을 때만 다시 넣는다."""
    if not docs:
        return 0
    signature = _signature(docs)
    marker = store_path() / "docs.sig"
    collection = _collection(DOCS)
    if marker.is_file() and marker.read_text(encoding="utf-8").strip() == signature and collection.count() > 0:
        return collection.count()
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict] = []
    for doc in docs:
        meta = getattr(doc, "metadata", {}) or {}
        text = str(getattr(doc, "page_content", "") or "").strip()
        if len(text) < 30:
            continue
        source = str(meta.get("source") or "")[:180]
        title = str(meta.get("title") or "")[:180]
        part = int(meta.get("part") or 0)
        ids.append(_doc_id(source, title, part))
        documents.append(text[:4000])
        metadatas.append({"source": source, "title": title, "part": part})
    keep = set(ids)
    existing = collection.get(include=[])
    stale = [item for item in existing.get("ids", []) if item not in keep]
    if stale:
        collection.delete(ids=stale)
    if ids:
        collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(signature, encoding="utf-8")
    return len(ids)


def search_documents(query: str, k: int = 4, min_similarity: float = 0.42) -> list[dict]:
    query = (query or "").strip()
    if not query:
        return []
    collection = _collection(DOCS)
    count = collection.count()
    if count <= 0:
        return []
    raw = collection.query(
        query_texts=[query],
        n_results=min(k, count),
        include=["documents", "metadatas", "distances"],
    )
    hits: list[dict] = []
    documents = (raw.get("documents") or [[]])[0]
    metadatas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]
    for document, meta, distance in zip(documents, metadatas, distances):
        if not document or not isinstance(meta, dict):
            continue
        similarity = 1.0 - float(distance)
        if similarity < min_similarity:
            continue
        hits.append(
            {
                "text": document,
                "source": str(meta.get("source") or ""),
                "title": str(meta.get("title") or ""),
                "part": int(meta.get("part") or 0),
                "score": round(similarity, 4),
            }
        )
    hits.sort(key=lambda item: item["score"], reverse=True)
    return hits[:k]


def sync_memory(items: list[dict]) -> None:
    rows = [item for item in items if item.get("question") and item.get("answer")]
    collection = _collection(MEMORY)
    ids = [str(item.get("id") or hashlib.sha1(str(item["question"]).encode("utf-8")).hexdigest()) for item in rows]
    keep = set(ids)
    existing = collection.get(include=[])
    stale = [item for item in existing.get("ids", []) if item not in keep]
    if stale:
        collection.delete(ids=stale)
    if not rows:
        return
    documents = []
    metadatas = []
    for item in rows:
        similar = " / ".join(str(line) for line in item.get("similar_questions") or [])
        documents.append(f"{item.get('question')} {similar}".strip()[:2000])
        metadatas.append(
            {
                "question": str(item.get("question") or "")[:500],
                "answer": str(item.get("answer") or "")[:1500],
                "similar": similar[:500],
            }
        )
    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def search_memory_vectors(query: str, k: int = 2, min_similarity: float = 0.5) -> list[tuple[float, dict]]:
    query = (query or "").strip()
    if not query:
        return []
    collection = _collection(MEMORY)
    count = collection.count()
    if count <= 0:
        return []
    raw = collection.query(
        query_texts=[query],
        n_results=min(k, count),
        include=["metadatas", "distances"],
    )
    hits: list[tuple[float, dict]] = []
    metadatas = (raw.get("metadatas") or [[]])[0]
    distances = (raw.get("distances") or [[]])[0]
    for meta, distance in zip(metadatas, distances):
        if not isinstance(meta, dict):
            continue
        similarity = 1.0 - float(distance)
        question = str(meta.get("question") or "")
        answer = str(meta.get("answer") or "")
        if similarity < min_similarity or not question or not answer:
            continue
        similar = [line.strip() for line in str(meta.get("similar") or "").split(" / ") if line.strip()]
        hits.append(
            (
                round(similarity, 4),
                {"question": question, "answer": answer, "similar_questions": similar[:6]},
            )
        )
    hits.sort(key=lambda item: item[0], reverse=True)
    return hits[:k]
