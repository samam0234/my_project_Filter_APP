# bugfix/deep-quota-kst → develop 병합 / `328ddaf`

> 브랜치: `develop`  
> 작성일: `2026-10-12 21:57`  
> 작성자: `agent`  
> 파일명: `261012_2157_328ddaf_merge-deep-quota-kst_develop.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `merge: bugfix/deep-quota-kst into develop (no-ff)` |
| **커밋 번호 (SHA)** | `328ddaf3a68d9a9f6c5bea4cf1376700da7668a7` |
| **짧은 SHA** | `328ddaf` |
| **브랜치** | `develop` |
| **부모 커밋** | `7859c14`, `fdfe60f` |

## 2. 주 커밋 내용

- `bugfix/deep-quota-kst`를 `develop`에 `--no-ff`로 병합했다.
- 깊이 추론 날짜를 UTC+9로 센다.
- 수정 커밋은 `d4647e0`다. 충돌은 없었다.

## 3. 상세 내용

### 3.1 배경 / 목적
안내 가상환경에 시간대 데이터가 없어 횟수 모듈이 기동하지 못했다. develop에 직접 고치지 않고 수정 브랜치를 병합했다.

### 3.2 변경 범위
- 추가된 경로: 커밋 기록
- 수정된 경로: `Portfolio/ai/deep_quota.py`, 테스트
- 삭제된 경로: 없음

### 3.3 기술 포인트
한국은 서머타임이 없다. 오늘 사용 10번은 그대로다.

### 3.4 의도적으로 하지 않은 것
tzdata 설치, main 병합, 푸시.

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 로컬 실행 확인
- [ ] Docker 확인
- [x] API/UI 스모크
- 결과 서술: 안내를 5057에 띄워 오늘 남은 횟수 0을 확인했다. 챗 화면에서 뇌 버튼은 눌리지 않고 자정 안내 상자가 나왔다. 모델 버튼은 e4b에서 12b로 바뀌고 질문은 보내지 않았다.

### 4.2 부작용 / 리스크
이미 5055나 5056에서 옛 코드로 떠 있는 안내 프로세스는 이 병합을 모른다.

### 4.3 후속 작업
develop을 main에 병합한다. 푸시는 이번 요청에 없다.

### 4.4 관련 문서
- `docs/branchs/commits/261012_2156_d4647e0_deep-quota-kst_bugfix-deep-quota-kst.md`
