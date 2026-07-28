# 컷앤킵 Grok 프로젝트 규칙

이 파일은 `.grok/rules/` 에 있어 Grok이 프로젝트 규칙으로 로드한다.

전체 스킬: `.agents/skills/cutnkeep/SKILL.md`  
에이전트 요약: 루트 `AGENTS.md`

## 핵심

1. 커밋: **type/scope 영어**, **제목 요약·본문·바닥글 한국어**  
   - ✅ `feat(tts): 음성 인식 추가`  
   - ❌ `feat(llm): add to engine`  
2. **커밋 기록 (필수):** `docs/branchs/commits/` 에 md **무조건** 남김  
   - 커밋 전 또는 직후 · 템플릿 `docs/branchs/TEMPLATE.md`  
   - `docs/commits/` 경로 **사용 금지** · 기록 생략 금지  
3. 작업 브랜치: `feature/*`  
4. develop/main 병합: **`git merge --no-ff` 필수**  
5. OpenCV 코드: `backend/app/services/` (별도 루트 폴더 아님)  
6. Python 의존성: 루트 `requirements.txt` / `requirements.docker.txt`  
7. 모델: **YOLO26s-seg** + Ollama gemma4:e4b  
   - 전략: `docs/plan/AI_MODEL_STRATEGY.md`  
   - n→s 전환: `docs/plan/YOLO26S_DEFAULT.md`  
