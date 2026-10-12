"""루트 data/feedback 의 확인된 문장을 data/chroma 에 넣는다.

의사 라벨과 파이프라인 실패 사진은 넣지 않는다. 그 문장은 해석 예시로 쓰면
정확도가 내려간 기록이 있다. 이 색인은 문장 해석이 확인되지 않은 필드를
따라가지 않도록, 사용자가 맞다고 한 문장과 교정만 꺼내는 저장소다.

실행 (저장소 루트):
    python scripts/chroma_feedback.py
    python scripts/chroma_feedback.py --query "사람 지워줘"
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.chroma_embed import embedding_function

COLLECTION = "verified_feedback"
_LOCK = threading.Lock()
_CLIENTS: dict[str, object] = {}


def chroma_dir(path: Path | None = None) -> Path:
    return path or (ROOT / "data" / "chroma")


def feedback_dir(path: Path | None = None) -> Path:
    return path or (ROOT / "data" / "feedback")


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def _answer(raw) -> str | None:
    if isinstance(raw, str):
        text = raw.strip()
        if "{" not in text:
            return None
        raw = text[text.find("{") : text.rfind("}") + 1]
        try:
            raw = json.loads(raw)
        except json.JSONDecodeError:
            return None
    if not isinstance(raw, dict):
        return None
    return json.dumps(raw, ensure_ascii=False, separators=(",", ":"))


def load_verified(folder: Path) -> list[dict]:
    """교정·좋아요만. 같은 문장이면 교정을 남긴다."""
    found: dict[str, dict] = {}
    if not folder.is_dir():
        return []
    priority = {"like": 1, "correction": 2}
    for path in sorted(folder.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        prompt = payload.get("prompt") or meta.get("prompt")
        if not isinstance(prompt, str) or not prompt.strip():
            continue
        source = str(payload.get("source") or meta.get("source") or "user")
        if source == "pipeline_failure":
            continue
        vote = str(payload.get("vote") or "").lower()
        if vote == "dislike":
            answer, kind = _answer(payload.get("comment")), "correction"
        elif vote == "like":
            answer, kind = _answer(meta.get("parsed_prompt") or payload.get("parsed_prompt")), "like"
        else:
            continue
        if not answer:
            continue
        key = _normalize(prompt)
        row = {"prompt": prompt.strip(), "answer": answer, "source": kind}
        current = found.get(key)
        if current is None or priority[kind] >= priority[current["source"]]:
            found[key] = row
    return list(found.values())


def _client(path: Path):
    import chromadb
    from chromadb.config import Settings

    path.mkdir(parents=True, exist_ok=True)
    key = str(path.resolve())
    with _LOCK:
        client = _CLIENTS.get(key)
        if client is None:
            client = chromadb.PersistentClient(
                path=key,
                settings=Settings(anonymized_telemetry=False),
            )
            _CLIENTS[key] = client
        return client


def _collection(path: Path):
    return _client(path).get_or_create_collection(
        name=COLLECTION,
        embedding_function=embedding_function(),
        metadata={"hnsw:space": "cosine"},
    )


def _row_id(prompt: str) -> str:
    return hashlib.sha1(_normalize(prompt).encode("utf-8")).hexdigest()


def rebuild(folder: Path | None = None, store: Path | None = None) -> int:
    """확인된 피드백을 다시 넣고, 파일에서 사라진 문장은 색인에서 뺀다."""
    rows = load_verified(feedback_dir(folder))
    collection = _collection(chroma_dir(store))
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
            metadatas=[{"answer": row["answer"][:2000], "source": row["source"]} for row in rows],
        )
    return len(rows)


def search(query: str, k: int = 3, min_similarity: float = 0.55, store: Path | None = None) -> list[dict]:
    """가까운 확인 문장. 점수는 코사인 유사도."""
    query = (query or "").strip()
    if not query:
        return []
    collection = _collection(chroma_dir(store))
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
    hits: list[dict] = []
    for document, meta, distance in zip(documents, metadatas, distances):
        if not document or not isinstance(meta, dict):
            continue
        similarity = 1.0 - float(distance)
        if similarity < min_similarity:
            continue
        answer = str(meta.get("answer") or "")
        source = str(meta.get("source") or "")
        if not answer or source not in {"correction", "like"}:
            continue
        hits.append(
            {
                "prompt": document,
                "answer": answer,
                "source": source,
                "score": round(similarity, 4),
            }
        )
    hits.sort(key=lambda item: item["score"], reverse=True)
    return hits[:k]


def main() -> None:
    parser = argparse.ArgumentParser(description="확인된 피드백을 data/chroma 에 색인한다.")
    parser.add_argument("--query", default="", help="색인 후 이 문장과 가까운 예시를 출력한다.")
    parser.add_argument("--k", type=int, default=3)
    args = parser.parse_args()
    count = rebuild()
    print(f"verified_feedback {count}건 → {chroma_dir()}")
    if args.query:
        for hit in search(args.query, k=args.k):
            print(f"{hit['score']:.3f} [{hit['source']}] {hit['prompt']}")


if __name__ == "__main__":
    main()
