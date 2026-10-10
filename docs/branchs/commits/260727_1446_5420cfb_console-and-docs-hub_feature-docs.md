# Ops console + documentation hub / `5420cfb`

> 브랜치: `feature/docs`  
> 작성일: `2026-07-27`  
> 작성자: project

## 1. 제목 / 커밋 번호

| 항목 | 내용 |
|------|------|
| **제목 (subject)** | `feat(docs): add ops console app and documentation hub folders` |
| **커밋 번호 (SHA)** | `5420cfb` (전체는 git log 참고) |
| **짧은 SHA** | `5420cfb` |
| **브랜치** | `feature/docs` |
| **부모 커밋** | `8157388` |

## 2. 주 커밋 내용

- 루트 `console/` React+TS 운영 관리자 앱 추가 (포트 5174)
- docs 허브 폴더 8종 구성 및 README/본문 채움
- branchs 커밋 템플릿 + 기존 커밋 상세 기록
- 루트 README / PROJECT_STRUCTURE 에 console 반영

## 3. 상세 내용

### 3.1 배경 / 목적
운영 콘솔이 누락되어 있었고, 문서가 plan 위주로만 존재해 운영·학습·검증 기록을 체계화할 필요가 있었다.

### 3.2 변경 범위
- 추가: `console/**`, `docs/Architecture`, `branchs`, `find_debug`, `guidance`, `trainings`, `repeater`, `vaildates`, `web_management`
- 수정: `README.md`, `.env.example`, `docs/plan/PROJECT_STRUCTURE.md`

### 3.3 기술 포인트
- Console: Job/Health API 폴링, 대시보드 집계
- branchs TEMPLATE: 제목·주내용·상세·결과 4단 구조 강제

### 3.4 의도적으로 하지 않은 것
- Console 인증
- Console Docker Compose 서비스 등록
- package-lock (로컬 npm install 시 생성)

## 4. 커밋 관련 결과

### 4.1 동작 결과
- [x] 코드/문서 커밋 완료
- [ ] console `npm install && npm run dev` 로컬 검증 (배포 전 권장)

### 4.2 부작용 / 리스크
- console 의존성 lockfile 미포함 가능 → 첫 install 필요

### 4.3 후속 작업
- develop merge / push
- console 인증 및 compose 서비스화

### 4.4 관련 문서
- `docs/README.md`
- `docs/guidance/console-admin.md`
- `docs/branchs/TEMPLATE.md`
