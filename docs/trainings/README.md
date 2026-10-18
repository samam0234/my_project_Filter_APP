# trainings — 배운 것 정리

> 코드 커밋과 별개로, **왜 이렇게 만들었는지** · 만들면서 무엇을 배웠는지를 남기는 노트.

"모델 학습(training)"이 아니라 "공부(training)" 노트다. 모델 학습 코드는 [`../../training/`](../../training/README.md)에, 실험 수치는 [`../vaildates/`](../vaildates/README.md)에 있다.

## 목록

| 파일 | 주제 | 배운 점 |
|------|------|---------|
| [phase1-pipeline.md](./phase1-pipeline.md) | Phase 1 이미지 파이프라인 | 프롬프트 → 구조화 → 전처리 → 세그 → 효과 → 검증 → 저장 흐름과 핵심 모듈(`workflows/nodes.py` · `effects.py` · `segmentation.py`) |
| [sqlalchemy-sqlite-mariadb.md](./sqlalchemy-sqlite-mariadb.md) | 이중 DB dialect | 같은 ORM 모델로 dialect 전환 · `JSON` 타입과 FK CASCADE 차이 · `create_all` vs Alembic |
| [docker-compose-projects.md](./docker-compose-projects.md) | Compose 프로젝트 격리 | 프로젝트 이름(`-p cut_and_keep`)으로 스택 · 네트워크 · 볼륨이 섞이지 않게 하는 법 |

## 이런 글을 여기에 쓴다

- 처음 써 본 기술의 핵심 개념과, 이 프로젝트에서 실제로 쓴 방식
- 여러 방법 중 하나를 고른 이유 (버린 방법과 그 이유 포함)
- 실패해서 알게 된 것 — 예: 두 프로세스가 같은 SQLite를 쓰면 깨진다, 학습 시드를 예시로 넣으면 점수가 내려갈 수 있다

수치가 있는 실험 결과는 여기가 아니라 [`../vaildates/`](../vaildates/README.md)에 둔다.

## 템플릿

```markdown
# Training: <주제>

## 배경 — 무엇을 하려 했나
## 핵심 개념
## 이 프로젝트에서 쓴 방식 (코드 경로)
## 고르지 않은 방법과 이유
## 남은 질문
```
