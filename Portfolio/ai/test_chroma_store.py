"""안내 Chroma — 가까운 문서 문단과 배운 질문만 꺼낸다."""

from __future__ import annotations

import os
from pathlib import Path


class _Doc:
    def __init__(self, text: str, source: str, title: str, part: int, path: str) -> None:
        self.page_content = text
        self.metadata = {"source": source, "title": title, "part": part, "path": path}


def test_documents_and_memory_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("PORTFOLIO_CHROMA_DIR", str(tmp_path / "chroma"))
    from chroma_store import ensure_documents, search_documents, search_memory_vectors, sync_memory

    folder = tmp_path / "docs"
    folder.mkdir()
    person = folder / "person.md"
    dog = folder / "dog.md"
    person.write_text("사람", encoding="utf-8")
    dog.write_text("강아지", encoding="utf-8")
    docs = [
        _Doc(
            "왼쪽에서 두 번째 사람만 지우고 나머지는 유지하는 해석 규칙입니다. 위치와 순서를 문장에서 가져옵니다.",
            "person.md",
            "사람 지우기",
            0,
            str(person),
        ),
        _Doc(
            "강아지만 남기고 배경을 블러 처리하는 효과입니다. 대상은 dog이고 효과는 blur입니다. 다른 동물은 대상이 아닙니다.",
            "dog.md",
            "강아지 블러",
            0,
            str(dog),
        ),
    ]
    assert ensure_documents(docs) == 2
    assert ensure_documents(docs) == 2
    hits = search_documents("오른쪽에서 두 번째 사람 지워 줘", k=2, min_similarity=0.2)
    assert hits[0]["title"] == "사람 지우기"
    assert search_documents("완전히 다른 외계 문장 zzz qqq", k=2, min_similarity=0.9) == []

    sync_memory(
        [
            {
                "id": "m0001",
                "question": "컷앤킵 안내 챗은 어떤 모델을 쓰나요",
                "answer": "안내 챗은 로컬 Ollama gemma4 12b를 쓰고 제품 기본 모델은 바꾸지 않습니다.",
                "similar_questions": ["안내 모델이 뭐야"],
            }
        ]
    )
    memory = search_memory_vectors("안내 챗 모델이 궁금합니다", k=1, min_similarity=0.2)
    assert memory[0][1]["question"].startswith("컷앤킵")
    assert "안내 모델이 뭐야" in memory[0][1]["similar_questions"]
    assert Path(os.environ["PORTFOLIO_CHROMA_DIR"]).is_dir()
