# Architecture

시스템 구조, 계층, 데이터 흐름, 배포 토폴로지를 정리하는 폴더입니다.

## 문서 목록

| 파일 | 설명 |
|------|------|
| [overview.md](./overview.md) | 전체 아키텍처 한눈에 보기 |
| [layers.md](./layers.md) | Router · Schema · Service · Repository · DB |
| [data-flow.md](./data-flow.md) | 요청~응답·피드백 데이터 흐름 |
| [apps.md](./apps.md) | frontend / console / backend 역할 분리 |
| [docker-topology.md](./docker-topology.md) | cut_and_keep Compose 토폴로지 |

## 관련 계획 문서

- `docs/plan/LOGIC_STRUCTURE.md`
- `docs/plan/PROJECT_STRUCTURE.md`
- `docs/plan/DATABASE.md`

## 작성 규칙

- 구현이 바뀌면 이 폴더를 먼저 갱신한다.
- 다이어그램은 ASCII 또는 mermaid를 사용한다.
