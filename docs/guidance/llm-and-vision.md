# LLM · 비전 모델 실행 가이드

전략 본문: [`docs/plan/AI_MODEL_STRATEGY.md`](../plan/AI_MODEL_STRATEGY.md)

---

## 비전: YOLO26s-seg (기본 스케일 s)

> 이전 문서의 YOLO26n 기본은 **s 로 통일**했다. 상세: [`docs/plan/YOLO26S_DEFAULT.md`](../plan/YOLO26S_DEFAULT.md)

```bash
# 가중치 위치 (예시)
# models/yolo26s-seg.pt  또는  models/yolo26s-seg.onnx

# ONNX export 예 (ultralytics 설치 환경)
# yolo export model=yolo26s-seg.pt format=onnx
```

`.env`:

```env
YOLO_MODEL_PATH=models/yolo26s-seg.pt
```

학습(세그 본선): [`training/README.md`](../../training/README.md)  
· `train_segment.py` · 클래스 `names` 와 `nodes.py` keywords 소문자 일치 필수.

Docker backend 의 Ollama 주소는 compose 가 `host.docker.internal:11434` 로 덮어쓸 수 있다  
→ [`CURRENT_STACK.md`](../plan/CURRENT_STACK.md).

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
