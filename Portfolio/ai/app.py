"""컷앤킵 포트폴리오 안내 서비스.

제품 FastAPI와 따로 뜬다. 화면의 대화 목록은 저장하지 않고, 학습 예시만 JSON에 남긴다.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request

from flask import Flask, jsonify, request

from deep_quota import reserve, status
from guide_graph import DEFAULT_MODEL, GUIDE_MODELS, guide, guide_model

app = Flask(__name__)
BASE = os.environ.get("OLLAMA_BASE_URL", "http://127.0.0.1:11434").rstrip("/")


def installed_models() -> tuple[list[str], str]:
    try:
        with urllib.request.urlopen(f"{BASE}/api/tags", timeout=4) as response:
            payload = json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return [], f"Ollama에 연결하지 못했습니다. {exc}"
    return [item.get("name", "") for item in payload.get("models", [])], ""


def has_model(names: list[str], model: str) -> bool:
    return any(name == model or name.startswith(model + ":") for name in names)


@app.get("/health")
def health():
    names, detail = installed_models()
    if detail:
        return jsonify(ok=False, ready=False, model=DEFAULT_MODEL, models={}, detail=detail), 503
    present = {model: has_model(names, model) for model in GUIDE_MODELS}
    ready = present[DEFAULT_MODEL]
    if not ready:
        shown = ", ".join(names) if names else "설치된 모델 없음"
        detail = f"{DEFAULT_MODEL} 이 없습니다. 설치됨: {shown}."
    else:
        detail = f"{DEFAULT_MODEL} 을 사용할 수 있습니다."
    return jsonify(ok=ready, ready=ready, model=DEFAULT_MODEL, models=present, detail=detail), (200 if ready else 503)


@app.get("/v1/deep")
def deep_count():
    return jsonify(status())


@app.post("/v1/guide")
def ask():
    data = request.get_json(silent=True) or {}
    model = guide_model(data.get("model"))
    names, detail = installed_models()
    if detail or not has_model(names, model):
        if not detail:
            detail = f"{model} 이 없습니다. 기본 모델은 {DEFAULT_MODEL} 입니다."
        return jsonify(detail=detail), 503
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
    deep = bool(data.get("deep"))
    if deep:
        gate = reserve()
        if not gate["ok"]:
            return jsonify(detail=gate["detail"], quota=gate), 429
    try:
        result = guide.invoke(
            {
                "question": cleaned[-1][1],
                "history": history,
                "sources": [],
                "route": "",
                "context": "",
                "answer": "",
                "deep": deep,
                "model": model,
            }
        )
    except Exception as exc:  # noqa: BLE001 — 모델 오류를 화면 문장으로 돌린다
        body = {"detail": f"모델 호출에 실패했습니다. {exc}"}
        if deep:
            body["quota"] = status()
        return jsonify(body), 502
    body = {"answer": result.get("answer") or "", "sources": result.get("sources") or []}
    if deep:
        body["quota"] = status()
    return jsonify(body)


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "5055")), debug=False)
