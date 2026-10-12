# develop → main 병합 / `974f3c2`

> 브랜치: `main`  
> 작성일: `2026-10-12 22:03`  
> 작성자: `agent`  
> 파일명: `261012_2203_974f3c2_merge-develop_main.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: develop into main (no-ff)` |
| **커밋 번호 (SHA)** | `974f3c23b7d16426a4e81b6dfdb599f6005cd1c0` |
| **짧은 SHA** | `974f3c2` |
| **브랜치** | `main` |
| **부모 커밋** | `2dfd0d4`, `c0411db` |

## 2. 주 커밋 내용

- 안내 챗 네 작업을 담은 `develop`을 `main`에 `--no-ff`로 붙였다.
- 깊이 추론 횟수는 한국 시간 오전 12시 전에는 다시 채워지지 않는다.
- 기본 모델은 `gemma4:e4b`이고, 보내기 위 버튼으로 `gemma4:12b`를 고른다.
- 설명 사이트 헤더와 카드 모양을 정리했다.
- 기능 브랜치를 main에 직접 붙이지 않았다.

## 3. 상세 내용

### 3.1 배경 / 목적
사용자가 develop 병합 다음 main 병합을 요청했다. 릴리스 브랜치, 태그, 푸시는 요청에 없다.

### 3.2 변경 범위
- 추가된 경로: `Portfolio/ai/deep_quota.py`, 테스트, 브랜치 기록
- 수정된 경로: 안내 챗, 모델 선택, 사이트 화면, `docs/branchs/README.md`
- 삭제된 경로: 없음

### 3.3 기술 포인트
develop 병합은 `2a6e3ba`, `10855c6`, `7859c14`, `328ddaf`다. 그 기록 커밋은 `c0411db`다. main 병합 충돌은 없었다. 날짜는 UTC+9 고정 시차다.

### 3.4 의도적으로 하지 않은 것
푸시, 서버 재배포, 태그, `release/*`, 제품 `.env` 변경, 모델 pull, tzdata 설치.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [x] API/UI 스모크
- 결과 서술: 병합 전에 안내를 5057, 사이트를 5190에 띄워 확인했다. 오늘 남은 횟수는 0이고 뇌 버튼은 눌리지 않으며 자정 안내 상자가 나왔다. 모델 버튼은 e4b에서 12b로 바뀌고 질문은 보내지 않았다. 확인용 프로세스는 종료했다.

### 4.2 부작용 / 리스크
이미 5055나 5056에서 옛 코드로 떠 있는 안내 프로세스는 이 병합을 모른다. 오늘 사용 10번은 자정까지 유지된다.

### 4.3 후속 작업
이 기록 커밋 뒤 develop을 main에 fast-forward한다. 푸시는 이번 요청에 없다.

### 4.4 관련 문서
- `docs/branchs/commits/261012_2153_2a6e3ba_merge-deep-quota-hold_develop.md`
- `docs/branchs/commits/261012_2154_10855c6_merge-guide-model_develop.md`
- `docs/branchs/commits/261012_2155_7859c14_merge-portfolio-look_develop.md`
- `docs/branchs/commits/261012_2157_328ddaf_merge-deep-quota-kst_develop.md`
