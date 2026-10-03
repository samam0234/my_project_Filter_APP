# data — 학습 공유 데이터

백엔드가 **기록**하고 `training/`·`scripts/` 가 **읽는** 학습 재료를 둔다.
업로드 이미지·SQLite 같은 서비스 런타임 데이터는 [`backend/data/`](../backend/data/README.md) 에 있다.

## 하위 디렉터리

| 경로 | 쓰는 쪽 | 읽는 쪽 | Git |
|------|---------|---------|-----|
| `feedback/` | backend (`FeedbackService`: 👍/👎·파이프라인 실패) | `training/lora`, `scripts/pseudo_labeling.py` | 내용 ignore |
| `pseudo_labels/` | `scripts/pseudo_labeling.py` | `training/lora`, YOLO 재학습 | 내용 ignore |
| `mariaDB_datas/` | Docker MariaDB (`docker-compose.yml` bind mount) | MariaDB 컨테이너만 | **전체 ignore** — 비어 있는 채로 시작, `.gitkeep` 금지 |

## 설정 (저장소 루트 기준 상대 경로)

```env
FEEDBACK_DIR=data/feedback
PSEUDO_LABEL_DIR=data/pseudo_labels
```

Docker Compose 는 `./data/feedback`·`./data/pseudo_labels` 를
컨테이너 `/app/data/feedback`·`/app/data/pseudo_labels` 에 마운트한다.

## 정책

- 피드백 케이스는 학습 루프용으로 보관한다 (업로드와 달리 cleanup 대상 아님).
- **비밀·개인 식별 원본**을 장기 두지 않도록 운영 정책을 정할 것.

## 관련 문서

- `docs/plan/DATABASE.md`
- `training/lora/README.md`
