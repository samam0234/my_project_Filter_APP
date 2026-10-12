"""포트폴리오 안내 그래프.

이해 → 문서 검색과 배운 대화 검색 → 초안 → 필요하면 수정 → JSON에 학습.
화면의 대화 목록은 브라우저가 가진다. 학습 JSON은 데이터베이스가 아니다.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.retrievers import BaseRetriever
from langchain_ollama import ChatOllama
from langgraph.graph import END, StateGraph
from pydantic import PrivateAttr
from rank_bm25 import BM25Okapi
from typing_extensions import TypedDict

from rag_memory import format_examples, remember_exchange, search_memory

ROOT = Path(__file__).resolve().parents[1]
DOC_DIRS = [ROOT / "markdown"]
EXTRA = [
    ROOT.parent / "docs" / "HANDOVER.md",
    ROOT.parent / "docs" / "FEATURES.md",
    ROOT.parent / "docs" / "WORKFLOW.md",
]

ROUTES = {
    "frontend": ("프론트", "화면", "작업실", "vite", "회원가입", "배치", "계정"),
    "console": ("콘솔", "검수", "관리자", "학습 데이터", "어드민"),
    "backend": ("백엔드", "fastapi", "api", "서버", "mariadb", "배포", "세션"),
    "ai": ("yolo", "ollama", "lora", "rag", "langchain", "langgraph", "모델", "세그", "인페인트"),
    "data": ("erd", "테이블", "스프레드시트", "signup", "데이터베이스", "db", "학습 db"),
}
ROUTE_FILES = {
    "frontend": ("02-frontend",),
    "console": ("03-console",),
    "backend": ("04-backend", "HANDOVER"),
    "ai": ("05-ai", "FEATURES"),
    "data": ("08-erd", "09-spreadsheet", "DATABASE"),
    "overview": ("01-overview", "06-project", "HANDOVER", "FEATURES"),
}
# 말투를 문서의 고유명사로 끌어올린다. 검색에만 쓰고, 사실 자체는 문서에서 가져온다.
EXPANSIONS = (
    (("오픈", "보캐브", "열린 어휘"), "OPEN_VOCAB Grounding DINO SAM2"),
    (("손님", "비로그인", "게스트"), "게스트 회원 기록 저장"),
    (("회원가입", "이메일", "인증"), "signup_pending 코드"),
    (("데이터베이스", "db", "디비", "마리아"), "서비스 DB 학습 DB MariaDB"),
    (("지우기", "인페인트", "메우"), "LaMa Telea inpaint"),
    (("영상", "gif", "지프", "동영상"), "mp4 배경판"),
    (("배치",), "batch_jobs 500"),
    (("콘솔", "관리자", "어드민"), "검수 루프백 CONSOLE"),
    (("워커", "cloudflare", "터널"), "Worker 524 Ollama"),
    (("yolo", "욜로", "세그", "마스크"), "YOLO26m-seg SegFormer"),
    (("모델", "llm", "올라마", "젬마", "gemma"), "gemma4:e4b gemma4:12b"),
    (("학습", "rag", "로라", "lora", "피드백"), "learning_samples LangChain"),
    (("랑그래프", "langgraph", "파이프라인"), "LangGraph prompt_analyzer segmentor"),
    (("랭체인", "langchain"), "LangChain PROMPT_CHAIN"),
)

SYSTEM = (
    "너는 컷앤킵 포트폴리오를 설명하는 안내자다. "
    "독자는 이 프로젝트를 검토하는 사람이다.\n"
    "규칙:\n"
    "- 제공된 문서에 적힌 사실만 말한다. 없는 수치, 기능, 일정, 사람 이름은 만들지 않는다.\n"
    "- 한국어 설명문으로 쓴다. 먼저 질문에 답하고, 이어서 이유와 범위, 문서에 있는 한계를 말한다. 보통 4~7문장.\n"
    "- 고유명사는 문서에 적힌 표기 그대로 쓰고, 뒤의 조사는 받침에 맞게 쓴다.\n"
    "- 파일 이름, 경로, 헤더 기호, 근거 줄은 답에 넣지 않는다.\n"
    "- 문서가 예정이라고 쓰지 않은 일을 앞으로의 계획으로 단정하지 않는다.\n"
    "- 답이 된 뒤에는 문서가 부족하다는 변명을 붙이지 않는다.\n"
    "- 같은 사실이 어긋나면 HANDOVER와 FEATURES를 우선한다.\n"
    "- 이전 대화가 있으면 그 대상을 이어서 설명한다. 대화와 문서가 충돌하면 문서를 따른다.\n"
    "- 이전 안내 예시는 말투와 빠진 점을 보완할 때만 쓴다. 예시와 문서가 다르면 문서를 따른다.\n"
    "- 문서가 부족하면 확인된 범위만 말하고, 무엇이 문서에 없는지 한 문장으로 밝힌다.\n"
    "- 사진 처리를 실행해 주지 않고, 공격이나 우회 절차는 거절한다."
)


class GuideState(TypedDict, total=False):
    question: str
    history: str
    route: str
    search_query: str
    context: str
    sources: list[str]
    examples: str
    draft: str
    issues: str
    revised: bool
    answer: str
    memory_id: str
    deep: bool


def _windows(body: str) -> list[str]:
    body = body.strip()
    if len(body) <= 1100:
        return [body] if len(body) >= 30 else []
    chunks: list[str] = []
    size, overlap = 900, 180
    start = 0
    while start < len(body):
        chunks.append(body[start : start + size])
        nxt = start + size - overlap
        if nxt <= start:
            break
        start = nxt
    return chunks


def _chunks(path: Path) -> list[Document]:
    text = path.read_text(encoding="utf-8")
    parts = re.split(r"\n(?=#{1,3} )", text)
    docs: list[Document] = []
    weight = 1.12 if path.name in {"HANDOVER.md", "FEATURES.md"} else 1.0
    for part in parts:
        part = part.strip()
        if len(part) < 30:
            continue
        heading = part.splitlines()[0].lstrip("# ").strip()[:120]
        for index, window in enumerate(_windows(part)):
            content = window if window.startswith("#") else f"{heading}\n{window}"
            docs.append(
                Document(
                    page_content=content,
                    metadata={
                        "source": path.name,
                        "title": heading,
                        "path": str(path),
                        "part": index,
                        "weight": weight,
                    },
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
    found = re.findall(r"[가-힣]{2,}|[A-Za-z0-9_.:/-]{2,}", text.lower())
    return found or ["empty"]


def _expand(question: str) -> str:
    lowered = question.lower()
    extra: list[str] = []
    for keys, words in EXPANSIONS:
        if any(key.lower() in lowered for key in keys):
            extra.append(words)
    return f"{question} {' '.join(extra)}".strip()


def _focus(question: str, history: str) -> str:
    text = question.strip()
    short = len(text) < 16 or bool(re.match(r"^(그|저|왜|그럼|더|자세히|그건|그게)", text))
    if not short:
        return text
    previous = ""
    for line in reversed((history or "").splitlines()):
        if line.startswith("user:"):
            previous = line.split(":", 1)[1].strip()
            break
    return f"{previous} {text}".strip() if previous else text


class PortfolioRetriever(BaseRetriever):
    """BM25, 글자 2-gram, 제목 일치에 Chroma 글자 벡터를 보탠다. 임베딩 모델은 받지 않는다."""

    documents: list[Document]
    k: int = 8
    _bm25: BM25Okapi = PrivateAttr()
    _token_cache: list[list[str]] = PrivateAttr()
    _gram_cache: list[set[str]] = PrivateAttr()
    _title_cache: list[set[str]] = PrivateAttr()

    def model_post_init(self, context) -> None:
        self._token_cache = [_tokens(doc.page_content) for doc in self.documents]
        self._gram_cache = [_grams(doc.page_content) for doc in self.documents]
        self._title_cache = [_grams(str(doc.metadata.get("title", ""))) for doc in self.documents]
        self._bm25 = BM25Okapi(self._token_cache)

    def search(self, query: str, route: str = "", k: int | None = None) -> list[tuple[float, Document]]:
        limit = k or self.k
        qgrams = _grams(query)
        tgrams = _grams(" ".join(_tokens(query)[:12]))
        bm = self._bm25.get_scores(_tokens(query))
        top = max((float(score) for score in bm), default=1.0) or 1.0
        phrases = [piece for piece in re.findall(r"[가-힣]{2,}|[A-Za-z0-9_.:/-]{3,}", query) if len(piece) >= 2]
        ranked: list[tuple[float, Document]] = []
        files = ROUTE_FILES.get(route, ())
        for index, doc in enumerate(self.documents):
            overlap = len(qgrams & self._gram_cache[index]) / len(qgrams) if qgrams else 0.0
            title_hit = len(tgrams & self._title_cache[index]) / len(tgrams) if tgrams else 0.0
            source = str(doc.metadata.get("source", ""))
            bonus = 0.06 if any(name.lower() in source.lower() for name in files) else 0.0
            phrase_hits = sum(1 for phrase in phrases if phrase.lower() in doc.page_content.lower())
            phrase = phrase_hits / len(phrases) if phrases else 0.0
            weight = float(doc.metadata.get("weight") or 1.0)
            score = weight * (0.46 * float(bm[index]) / top + 0.28 * overlap + 0.14 * title_hit + 0.12 * phrase + bonus)
            if score > 0:
                ranked.append((score, doc))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked[:limit]

    def _get_relevant_documents(self, query: str, *, run_manager=None) -> list[Document]:
        route = ""
        if "\nroute:" in query:
            query, _, route = query.partition("\nroute:")
            route = route.strip()
        found = self.search(query, route, self.k)
        return [doc for _, doc in found] or self.documents[:2]


def understand(state: GuideState) -> GuideState:
    question = state.get("question", "")
    focused = _focus(question, state.get("history", ""))
    text = focused.lower()
    best, best_hits = "overview", 0
    for name, words in ROUTES.items():
        hits = sum(1 for word in words if word.lower() in text)
        if hits > best_hits:
            best, best_hits = name, hits
    return {"route": best, "search_query": _expand(focused)}


def _chroma_passages(query: str) -> list[tuple[float, Document]]:
    """Chroma가 고른 문서 조각. 실패하면 빈 목록이라 BM25 결과만 남는다."""
    try:
        from chroma_store import ensure_documents, search_documents

        ensure_documents(state_retriever.documents)
        found = search_documents(query, k=4, min_similarity=0.42)
    except Exception:
        return []
    passages: list[tuple[float, Document]] = []
    for hit in found:
        passages.append(
            (
                float(hit["score"]),
                Document(
                    page_content=hit["text"],
                    metadata={"source": hit["source"], "title": hit["title"], "part": hit["part"], "weight": 1.0},
                ),
            )
        )
    return passages


def _with_memory(question: str) -> list[tuple[float, dict]]:
    remembered = search_memory(question, k=2)
    try:
        from chroma_store import search_memory_vectors

        extra = search_memory_vectors(question, k=2, min_similarity=0.5)
    except Exception:
        extra = []
    seen = {str(item.get("question") or "") for _, item in remembered}
    for score, item in extra:
        question_text = str(item.get("question") or "")
        if not question_text or question_text in seen:
            continue
        seen.add(question_text)
        remembered.append((score, item))
    return remembered[:3]


def retrieve(state: GuideState) -> GuideState:
    question = (state.get("question") or "").strip()
    expanded = (state.get("search_query") or "").strip()
    deep = bool(state.get("deep"))
    search_k, keep_n, char_cap = _bounds(deep)
    queries = [(question, 1.0)]
    if expanded and expanded != question:
        queries.append((expanded, 0.42))
    merged: dict[tuple[str, str, int], tuple[float, Document]] = {}
    route = state.get("route", "")
    for query, weight in queries:
        for score, doc in state_retriever.search(query, route, search_k):
            key = (str(doc.metadata.get("source")), str(doc.metadata.get("title")), int(doc.metadata.get("part") or 0))
            previous = merged.get(key)
            total = score * weight
            if previous is None:
                merged[key] = (total, doc)
            else:
                merged[key] = (previous[0] + total, doc)
    ranked = sorted(merged.values(), key=lambda item: item[0], reverse=True)
    diverse: list[tuple[float, Document]] = []
    deferred: list[tuple[float, Document]] = []
    per_file: dict[str, int] = {}
    for item in ranked:
        source = str(item[1].metadata.get("source"))
        if per_file.get(source, 0) >= 2:
            deferred.append(item)
            continue
        diverse.append(item)
        per_file[source] = per_file.get(source, 0) + 1
    ranked = diverse + deferred
    if not ranked:
        chroma_only = _chroma_passages(question)
        if chroma_only:
            ranked = chroma_only
        else:
            remembered = _with_memory(question)
            examples = format_examples(remembered)
            sources = ["rag_memory.json · 비슷한 안내"] if remembered else []
            return {"context": "", "sources": sources, "examples": examples}
    best = ranked[0][0] or 1.0
    kept: list[tuple[float, Document]] = []
    total = 0
    min_keep = 8 if deep else 3
    floor = 0.28 if deep else 0.45
    for score, doc in ranked:
        if len(kept) >= min_keep and score < best * floor:
            break
        if len(kept) >= keep_n or total > char_cap:
            break
        kept.append((score, doc))
        total += len(doc.page_content)
    present = {
        (str(doc.metadata.get("source")), str(doc.metadata.get("title")), int(doc.metadata.get("part") or 0))
        for _, doc in kept
    }
    added = 0
    for score, doc in _chroma_passages(question):
        key = (str(doc.metadata.get("source")), str(doc.metadata.get("title")), int(doc.metadata.get("part") or 0))
        if key in present or score < 0.55 or added >= 2 or total + len(doc.page_content) > char_cap:
            continue
        kept.append((score, doc))
        present.add(key)
        total += len(doc.page_content)
        added += 1
    blocks: list[str] = []
    sources: list[str] = []
    for index, (_, doc) in enumerate(kept, start=1):
        label = f"{doc.metadata.get('source')} · {doc.metadata.get('title')}"
        if label not in sources:
            sources.append(label)
        blocks.append(f"({index}) {label}\n{doc.page_content}")
    remembered = _with_memory(question)
    examples = format_examples(remembered)
    if remembered:
        sources.append("rag_memory.json · 비슷한 안내")
    return {"context": "\n\n".join(blocks), "sources": sources, "examples": examples}


def _message_text(result: object) -> str:
    if isinstance(result, str):
        return result.strip()
    text = getattr(result, "content", "") or ""
    if isinstance(text, list):
        text = "".join(part.get("text", "") if isinstance(part, dict) else str(part) for part in text)
    text = str(text).strip()
    if not text:
        extra = getattr(result, "additional_kwargs", {}) or {}
        text = str(extra.get("reasoning_content") or "").strip()
    return text


def _clean(text: str) -> str:
    kept: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("근거:") or stripped.startswith("출처:"):
            continue
        stripped = re.sub(r"[A-Za-z0-9_./\\-]+\.md", "", stripped)
        stripped = re.sub(r"(?:이|그)?\s*내용은.{0,80}?명시되어 있습니다\.?", "", stripped)
        stripped = re.sub(r"\s{2,}", " ", stripped)
        stripped = re.sub(r"\s+([,.:])", r"\1", stripped).strip(" ,;·")
        if stripped:
            kept.append(stripped)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(kept)).strip()


def _issues(answer: str, context: str, question: str) -> str:
    notes: list[str] = []
    ctx_numbers = set(re.findall(r"\d+(?:\.\d+)?", context))
    stray = [
        number
        for number in set(re.findall(r"\d+(?:\.\d+)?", answer))
        if number not in ctx_numbers and number not in {"1", "2", "3", "4", "5", "6", "7", "8", "9"}
    ]
    if stray:
        notes.append(f"문서에 없는 숫자 {', '.join(sorted(stray))} 를 빼라.")
    if "예정" in answer and "예정" not in context:
        notes.append("문서에 없는 예정 일정을 빼라. 지금 상태만 말해라.")
    if len(question) > 12 and len(answer) < 50 and len(context) > 200:
        notes.append("답이 짧다. 문서에 있는 이유와 범위를 4문장 이상으로 풀어라.")
    if any(word in answer for word in ("모르겠", "확인할 수 없", "문서에 없")) and len(context) > 400:
        qgrams = _grams(question)
        if qgrams and len(qgrams & _grams(context)) / len(qgrams) > 0.18:
            notes.append("문서에 관련 문장이 있다. 그 범위만 단정해서 다시 써라.")
    return " ".join(notes)


BASE_PREDICT = 800
BASE_CTX = 6144
DEEP_SCALE = 2.5


def _bounds(deep: bool) -> tuple[int, int, int]:
    """검색 개수, 채택 개수, 문서 글자 상한. 깊이 추론은 일반의 2.5배."""
    if not deep:
        return 12, 6, 5200
    return int(12 * DEEP_SCALE), int(6 * DEEP_SCALE), int(5200 * DEEP_SCALE)


def _llm(predict: int, ctx: int, reasoning: bool, timeout: int) -> ChatOllama:
    return ChatOllama(
        model=os.environ.get("OLLAMA_MODEL", "gemma4:12b"),
        base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        temperature=0.2,
        top_p=0.9,
        repeat_penalty=1.08,
        num_ctx=ctx,
        num_predict=predict,
        # gemma4는 생각 토큰을 켜면 생성 한도를 생각만 쓰고 본문이 빈다.
        # 깊이 추론도 본문을 쓰고, 깊이는 검색·문맥·생성 길이를 2.5배로 둔다.
        reasoning=reasoning,
        client_kwargs={"timeout": timeout},
    )


llm = _llm(BASE_PREDICT, BASE_CTX, False, 100)
deep_llm = _llm(int(BASE_PREDICT * DEEP_SCALE), int(BASE_CTX * DEEP_SCALE), False, 540)
draft_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM),
            (
                "human",
                "분류: {route}\n\n이전 대화:\n{history}\n\n문서:\n{context}\n\n이전 안내 예시:\n{examples}\n\n질문:\n{question}",
            ),
        ]
    )
    | llm
    | StrOutputParser()
)
deep_draft_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SYSTEM + "\n- 이번 답은 깊이 추론이다. 문서 안의 이유, 예외, 한계를 일반 답보다 길게 펼친다.",
            ),
            (
                "human",
                "분류: {route}\n\n이전 대화:\n{history}\n\n문서:\n{context}\n\n이전 안내 예시:\n{examples}\n\n질문:\n{question}",
            ),
        ]
    )
    | deep_llm
    | StrOutputParser()
)
revise_chain = (
    ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM),
            (
                "human",
                "문서:\n{context}\n\n질문:\n{question}\n\n초안:\n{draft}\n\n고칠 점: {issues}\n"
                "초안을 고쳐서 최종 답만 다시 써라. 고칠 점을 언급하지 마라.",
            ),
        ]
    )
    | llm
    | StrOutputParser()
)
deep_revise_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                SYSTEM + "\n- 이번 답은 깊이 추론이다. 문서 안의 이유, 예외, 한계를 일반 답보다 길게 펼친다.",
            ),
            (
                "human",
                "문서:\n{context}\n\n질문:\n{question}\n\n초안:\n{draft}\n\n고칠 점: {issues}\n"
                "초안을 고쳐서 최종 답만 다시 써라. 고칠 점을 언급하지 마라.",
            ),
        ]
    )
    | deep_llm
    | StrOutputParser()
)


def draft(state: GuideState) -> GuideState:
    chain = deep_draft_chain if state.get("deep") else draft_chain
    raw = chain.invoke(
        {
            "route": state.get("route", "overview"),
            "history": state.get("history") or "(없음)",
            "context": state.get("context") or "(검색 결과 없음)",
            "examples": state.get("examples") or "(없음)",
            "question": state.get("question", ""),
        }
    )
    raw_text = _message_text(raw)
    cleaned = _clean(raw_text) or "문서에서는 답을 만들지 못했습니다. 질문을 더 구체적으로 적어 주세요."
    issues = _issues(cleaned, state.get("context", ""), state.get("question", ""))
    if state.get("deep") and len(cleaned) < 800:
        issues = (
            f"{issues} 깊이 추론이다. 문서에 있는 이유, 예외, 한계를 6문장 이상으로 풀어라. "
            "한 문단으로 끝내지 마라."
        ).strip()
    if ".md" in raw_text:
        issues = f"{issues} 파일 이름 없이 완전한 문장으로 다시 써라.".strip()
    return {"draft": cleaned, "answer": cleaned, "issues": issues}


def revise(state: GuideState) -> GuideState:
    chain = deep_revise_chain if state.get("deep") else revise_chain
    raw = chain.invoke(
        {
            "context": state.get("context") or "(검색 결과 없음)",
            "question": state.get("question", ""),
            "draft": state.get("draft") or "",
            "issues": state.get("issues") or "",
        }
    )
    cleaned = _clean(_message_text(raw))
    return {"answer": cleaned or state.get("draft") or "", "revised": True, "issues": ""}


def _after_draft(state: GuideState) -> str:
    if state.get("issues") and not state.get("revised"):
        return "revise"
    return "remember"


_SIMILAR_SWAPS = (
    ("오픈 보캐브", "열린 어휘"),
    ("열린 어휘", "오픈 보캐브"),
    ("비로그인 사용자", "로그인하지 않은 손님"),
    ("비로그인", "게스트"),
    ("데이터베이스", "DB"),
    ("운영 콘솔", "어드민 콘솔"),
    ("콘솔", "운영 콘솔"),
    ("기본 문장 모델", "기본 해석 모델"),
)


def _local_similar(question: str) -> list[str]:
    found: list[str] = []
    for source, target in _SIMILAR_SWAPS:
        if source in question and target not in question:
            found.append(question.replace(source, target))
    return found[:3]


def _parse_similar(text: str) -> list[str]:
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return []
    try:
        data = json.loads(match.group(0))
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    return [str(item).strip() for item in data if str(item).strip()]


_similar_llm = ChatOllama(
    model=os.environ.get("OLLAMA_MODEL", "gemma4:12b"),
    base_url=os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
    temperature=0.3,
    num_predict=180,
    reasoning=False,
    client_kwargs={"timeout": 60},
)
_similar_chain = (
    ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "같은 뜻을 묻는 한국어 질문만 만든다. 새 사실, 새 숫자, 새 기능 이름은 넣지 않는다. "
                "JSON 배열만 출력한다.",
            ),
            ("human", "질문: {question}\n\n답의 앞부분: {answer}\n\n같은 뜻의 질문 3개."),
        ]
    )
    | _similar_llm
    | StrOutputParser()
)


def remember(state: GuideState) -> GuideState:
    question = (state.get("question") or "").strip()
    answer = (state.get("answer") or "").strip()
    if len(question) < 8 or len(answer) < 40 or answer.startswith("문서에서는 답을 만들지 못했습니다"):
        return {}
    try:
        generated = _parse_similar(
            _message_text(
                _similar_chain.invoke({"question": question, "answer": answer[:400]})
            )
        )
        similar = _local_similar(question) + generated
        item_id = remember_exchange(
            question,
            answer,
            list(state.get("sources") or []),
            state.get("route") or "",
            similar,
        )
    except Exception:
        return {}
    return {"memory_id": item_id} if item_id else {}


def build_graph():
    graph = StateGraph(GuideState)
    graph.add_node("understand", understand)
    graph.add_node("retrieve", retrieve)
    graph.add_node("draft", draft)
    graph.add_node("revise", revise)
    graph.add_node("remember", remember)
    graph.set_entry_point("understand")
    graph.add_edge("understand", "retrieve")
    graph.add_edge("retrieve", "draft")
    graph.add_conditional_edges("draft", _after_draft, {"revise": "revise", "remember": "remember"})
    graph.add_edge("revise", "remember")
    graph.add_edge("remember", END)
    return graph.compile()


documents = load_documents()
state_retriever = PortfolioRetriever(documents=documents, k=8)
guide = build_graph()
