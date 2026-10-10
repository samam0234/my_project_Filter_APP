# 잔여 feature/* 를 develop 에 일괄 병합 / `af84350`

> 브랜치: `develop`  
> 작성일: `2026-07-28 15:45` (병합 웨이브 종료 시각 근사)  
> 작성자: `while`  
> 파일명: `260728_1545_af84350_merge-all-features-into-develop_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | 다수 `merge: feature/* into develop (no-ff)` (tip `af84350` = video) |
| **브랜치** | `develop` |
| **방식** | 각 feature 별 `git merge --no-ff` |

## 2. 병합한 브랜치 (순서)

`yolo` → `docs` → `opencv` → `llm` → `langgraph` → `feedback` → `batch` → `frontend` → `scripts` → `models` → `lora` → `sam2` → `video`  
(`feature/backend` 는 선행 `aaffa89` 에서 이미 포함)

## 3. 결과

- 모든 `feature/*` 가 develop 대비 **ahead=0** 상태였음
- 충돌 없이 완료, `origin/develop` 푸시됨

## 4. 비고

앵커 전용(lora/sam2/video) 포함. 이후 작업 시 feature 에서 develop 을 다시 맞출 것.
