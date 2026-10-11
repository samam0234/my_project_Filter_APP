"""포트폴리오 안내 그래프.

질문 분류 → 문서 검색 → Ollama 답변.
대화는 인자로만 받고 어디에도 저장하지 않는다.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from pydantic import PrivateAttr
from rank_bm25 import BM25Okapi
from typing_extensions import TypedDict

ROOT = Path(__file__).resolve().parents[1]
DOC_DIRS = [ROOT / "markdown"]
EXTRA = [
    ROOT.parent / "docs" / "HANDOVER.md",
    ROOT.parent / "docs" / "FEATURES.md",
    ROOT.parent / "docs" / "WORKFLOW.md",
]

ROUTES = {
    "frontend": ("프론트", "화면", "작업실", "vite", "회원가입", "배치 화면"),
    "console": ("콘솔", "검수", "관리자", "학습 데이터"),
    "backend": ("백엔드", "fastapi", "api", "서버", "mariadb", "배포"),
    "ai": ("yolo", "ollama", "lora", "rag", "langchain", "langgraph", "모델", "세그"),
    "data": ("erd", "테이블", "스프레드시트", "signup", "데이터베이스", "db", "학습 db"),
}


class GuideState(TypedDict, total=False):
    question: str
    history: str
    route: str
    context: str
    sources: list[str]
    answer: str


def _chunks(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"\n(?=#{1,3} )", text)
    docs: list[Document] = []
    for part in parts:
        part = part.strip()
        if len(part) < 40:
            continue
        title = part.splitlines()[0][:100]
        step = 1600
        for offset in range(0, len(part), step):
            body = part[offset : offset + step]
            docs.append(
                Document(
                    page_content=body,
                    metadata={"source": path.name, "title": title, "path": str(path)},
                )
            )
    return docs


def load_documents() -> list[Document]:
    docs: list[Document] = []
    for folder in DOC_DIRS:
        for path in sorted(folder.glob("*.md")):
            docs.extend(_chunks(path))
    for path in EXTRA:
        if path.is_file():
            docs.extend(_chunks(path))
    return docs


def _grams(text: str) -> set[str]:
    compact = re.sub(r"\s+", "", text.lower())
    if len(compact) < 2:
        return {compact} if compact else set()
    return {compact[i : i + 2] for i in range(len(compact) - 1)}


def _tokens(text: str) -> list[str]:
    return re.findall(r"[가-힣]{2,}|[A-Za-z0-9_./:-]{2,}", text.lower()) or ["empty"]


class PortfolioRetriever(BaseRetriever):
    """2-gram 겹침과 BM25를 더한다. 벡터 데이터베이스는 없다."""

    documents: list[Document]
    k: int = 5
    _bm25: BM25Okapi = PrivateAttr()

    def model_post_init(self, context) -> None:
        corpus = [_tokens(doc.page_content) for doc in self.documents]
        self._bm25 = BM25Okapi(corpus)

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        route = ""
        if "\nroute:" in query:
            query, _, route = query.partition("\nroute:")
            route = route.strip()
        qgrams = _grams(query)
        bm = self._bm25.get_scores(_tokens(query))
        top = max(bm) if len(bm) else 1
        top = top or 1
        ranked: list[tuple[float, Document]] = []
        for index, doc in enumerate(self.documents):
            grams = _grams(doc.page_content)
            overlap = len(qgrams & grams) / len(qgrams) if qgrams else 0
            bonus = 0.08 if route and route in doc.metadata.get("source", "").lower() else 0
            ranked.append((overlap + float(bm[index]) / top + bonus, doc))
        ranked.sort(key=lambda item: item[0], reverse=True)
        picked = [doc for score, doc in ranked[: self.k] if score > 0]
        return picked or [doc for _, doc in ranked[:2]]


def classify(state: GuideState) -> GuideState:
    text = state.get("question", "").lower()
    best = "overview"
    best_hits = 0
    for name, words in ROUTES.items():
        hits = sum(1 for word in words if word.lower() in text)
        if hits > best_hits:
            best, best_hits = name, hits
    return {"route": best}


def retrieve(state: GuideState) -> GuideState:
    retriever: PortfolioRetriever = state_retriever
    docs = retriever.invoke(f"{state.get('question', '')}\nroute:{state.get('route', '')}")
    blocks = []
    sources: list[str] = []
    for doc in docs:
        label = f"{doc.metadata.get('source')} · {doc.metadata.get('title')}"
        if label not in sources:
            sources.append(label)
        blocks.append(f"[{label}]\n{doc.page_content}")
    return {"context": "\n\n".join(blocks), "sources": sources}


def answer(state: GuideState) -> GuideState:
    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "너는 컷앤킵 포트폴리오 안내자다. 제공된 문서만 근거로 한국어로 답한다. "
                "문서에 없으면 없다고 말한다. 없는 기능, 없는 수치, 비밀 값을 만들지 않는다. "
                "사진 처리 방법을 실행해 주지 않고, 공격이나 우회 절차는 거절한다. "
                "답은 짧고 단정하게 쓴다. 마지막에 근거 파일 이름을 한 줄로 적는다.",
            ),
            (
                "human",
                "분류: {route}\n\n이전 대화:\n{history}\n\n문서:\n{context}\n\n질문:\n{question}",
            ),
        ]
    )
    chain = prompt | llm
    result = chain.invoke(
        {
            "route": state.get("route", "overview"),
            "history": state.get("history") or "(없음)",
            "context": state.get("context") or "(검색 결과 없음)",
            "question": state.get("question", ""),
        }
    )
    text = getattr(result, "content", "") or ""
    if isinstance(text, list):
        text = "".join(
            part.get("text", "") if isinstance(part, dict) else str(part) for part in text
        )
    text = str(text).strip()
    if not text:
        extra = getattr(result, "additional_kwargs", {}) or {}
        text = str(extra.get("reasoning_content") or "").strip()
    if not text:
        text = "문서에서는 답을 만들지 못했습니다. 질문을 더 짧게 다시 적어 주세요."
    return {"answer": text}


def build_graph():
    graph = StateGraph(GuideState)
    graph.add_node("classify", classify)
    graph.add_node("retrieve", retrieve)
    graph.add_node("answer", answer)
    graph.set_entry_point("classify")
    graph.add_edge("classify", "retrieve")
    graph.add_edge("retrieve", "answer")
    graph.add_edge("answer", END)
    return graph.compile()


documents = load_documents()
state_retriever = PortfolioRetriever(documents=documents, k=5)
llm = ChatOllama(
    model=os.environ.get("OLLAMA_MODEL", "gemma4:12b"),
    base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    temperature=0.1,
    num_predict=700,
    # gemma4는 기본으로 생각 토큰을 먼저 쓴다. 끄지 않으면 본문이 비는 경우가 있다.
    reasoning=False,
    client_kwargs={"timeout": 120},
)
guide = build_graph()
