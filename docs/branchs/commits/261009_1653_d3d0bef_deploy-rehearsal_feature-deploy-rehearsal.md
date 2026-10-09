# 배포 리허설 점검 스크립트 · 모델 묶음/체크섬 도구 / `d3d0bef1b70dbfac7498187cda6d9628458d00a3`

> 브랜치: `feature/deploy-rehearsal`  
> 작성일: `2026-10-09 16:53`  
> 작성자: `agent`  
> 파일명: `261009_1653_d3d0bef_deploy-rehearsal_feature-deploy-rehearsal.md`

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(deploy): 배포 리허설 점검 스크립트 · 모델 묶음/체크섬 도구` |
| **커밋 번호 (SHA)** | `d3d0bef1b70dbfac7498187cda6d9628458d00a3` |
| **짧은 SHA** | `d3d0bef` |
| **브랜치** | `feature/deploy-rehearsal` |
| **부모 커밋** | `b144c20` |

## 2. 주 커밋 내용

- `scripts/deploy_check.py` (remote · server)
- `scripts/models_bundle.py` (pack · verify)

## 3. 상세 내용

### 3.1 배경 / 목적
완성도 설명의 "실서버 · 도메인 배포 검증 안 함, 모델이 git 밖" 을 서버만 있으면 바로 돌릴 수 있는 도구로.

### 3.2 변경 범위
- 추가: 두 스크립트, `tests/unit/test_deploy_tools.py`
- 수정: `docs/guidance/https-deploy.md`(3-1절), `scripts/README.md`, `docs/FEATURES.md`, `.gitignore`(/dist/)

### 3.3 기술 포인트
- 리허설을 로컬 https compose 로 실제 실행해 확인 (실패 0 · 경고 1)
- Windows docker 출력 cp949 디코딩 오류 수정 (utf-8)

### 3.4 의도적으로 하지 않은 것
- 실제 도메인 · 실서버 배포 (사용자 결정)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 전체 테스트 444 통과
- [x] 로컬 https 리허설 통과, Docker 일반 모드로 복원

### 4.2 부작용 / 리스크
- 없음

### 4.3 후속 작업
- 실서버에서 remote · server 점검

### 4.4 관련 문서
- `docs/guidance/https-deploy.md`
