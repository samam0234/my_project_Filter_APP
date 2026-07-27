# LLM · 비전 모델 실행 가이드

전략 본문: [`docs/plan/AI_MODEL_STRATEGY.md`](../plan/AI_MODEL_STRATEGY.md)

---

## 비전: YOLO26n-seg

```bash
# 가중치 위치 (예시)
# models/yolo26n-seg.pt  또는  models/yolo26n-seg.onnx

# ONNX export 예 (ultralytics 설치 환경)
# yolo export model=yolo26n-seg.pt format=onnx
```

`.env`:

```env
YOLO_MODEL_PATH=models/yolo26n-seg.pt
```

---

## 로컬 LLM: Ollama Gemma 4 E4B

```bash
# Ollama 설치 후
ollama pull gemma4:e4b
ollama serve   # 기본 http://localhost:11434
ollama run gemma4:e4b
```

`.env`:

```env
LLM_PROVIDER=ollama
LLM_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma4:e4b
# OpenAI 호환 클라이언트 사용 시:
# LLM_BASE_URL=http://localhost:11434/v1
```

Phase 1 권장: **텍스트 프롬프트 → JSON** 만 E4B.  
마스크는 YOLO-seg. (E4B 이미지 입력은 Ollama 버전별 지원 확인 후)

---

## 고도화 LLM

### OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
# OPENAI_MODEL=gpt-4o-mini
```

### Gemini

```env
LLM_PROVIDER=gemini
GEMINI_API_KEY=...
# GEMINI_MODEL=gemini-2.0-flash
```

전환 후 동일 `prompt_analyzer` 계약(`ParsedPrompt`) 유지.

---

## Fallback

Ollama/API 실패 시: `workflows/nodes.py` 휴리스틱 파서 사용 (한국어 키워드 등).
