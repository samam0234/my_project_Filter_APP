"""컷앤킵 포트폴리오 안내 서비스.

제품 FastAPI와 따로 뜬다. 대화는 저장하지 않는다.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, request

from guide_graph import guide

app = Flask(__name__)
MODEL = os.environ.get("OLLAMA_MODEL", "gemma4:12b")
BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def model_status() -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(f"{BASE}/api/tags", timeout=4) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return False, f"Ollama에 연결하지 못했습니다. {exc}"
    names = [item.get("name", "") for item in payload.get("models", [])]
    ready = any(name == MODEL or name.startswith(MODEL + ":") for name in names)
    if ready:
        return True, f"{MODEL} 을 사용할 수 있습니다."
    shown = ", ".join(names) if names else "설치된 모델 없음"
    return False, f"{MODEL} 이 없습니다. 설치됨: {shown}. ollama pull {MODEL}"


@app.get("/health")
def health():
    ready, detail = model_status()
    return jsonify(ok=ready, ready=ready, model=MODEL, detail=detail), (200 if ready else 503)


@app.post("/v1/guide")
def ask():
    ready, detail = model_status()
    if not ready:
        return jsonify(detail=detail), 503
    data = request.get_json(silent=True) or {}
    messages = data.get("messages")
    if not isinstance(messages, list) or not messages:
        return jsonify(detail="messages가 필요합니다."), 400
    cleaned = []
    for item in messages[-8:]:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = str(item.get("content") or "").strip()
        if role in ("user", "assistant") and content:
            cleaned.append((role, content[:2000]))
    if not cleaned or cleaned[-1][0] != "user":
        return jsonify(detail="마지막 메시지는 사용자 질문이어야 합니다."), 400
    history = "\n".join(f"{role}: {content}" for role, content in cleaned[:-1]) or "(없음)"
    try:
        result = guide.invoke(
            {"question": cleaned[-1][1], "history": history, "sources": [], "route": "", "context": "", "answer": ""}
        )
    except Exception as exc:  # noqa: BLE001 — 모델 오류를 화면 문장으로 돌린다
        return jsonify(detail=f"모델 호출에 실패했습니다. {exc}"), 502
    return jsonify(answer=result.get("answer") or "", sources=result.get("sources") or [])


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5055")), debug=False)
