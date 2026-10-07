# vaildates — 검증 내용 정리

> 폴더명 표기는 요청 스펠링 `vaildates` 를 따름 (validate 의미).

기능·배포 전 검증 체크리스트와 결과를 기록한다.

## 목록

| 파일 | 설명 |
|------|------|
| [mvp-checklist.md](./mvp-checklist.md) | Phase 1 MVP 검증 항목 |
| [api-smoke.md](./api-smoke.md) | API 스모크 시나리오 |
| [console-checklist.md](./console-checklist.md) | 운영 콘솔 검증 |
| [ui-check-20261006.md](./ui-check-20261006.md) | 브라우저 직접 확인: 사용자 앱·콘솔 9개 흐름 (Playwright) |
| [ui-check-20261007.md](./ui-check-20261007.md) | 브라우저 직접 확인: 배치·영상·콘솔 배치 현황 포함 13개 흐름, 찾은 문제 4건 |
| [ui-check-20261007-console.md](./ui-check-20261007-console.md) | 브라우저 2차: 영상 페이지 재생(webm) · 콘솔 관리자 로그인·일반 회원 거절 · 회원 삭제 · 시스템/정리 미리 보기 포함 17개 흐름, 문제 0건 |
| [open-vocab-20261007.md](./open-vocab-20261007.md) | 오픈 보캐브(DINO+SAM2) 실가동 + 박스 임계값 측정(COCO 3,000쌍: 0.25→0.35 오검출 17.9%→7.4%, 재현율 −3.9%p) + `open_vocab_threshold_20261007.json` |
| [experiments-20261006.md](./experiments-20261006.md) | 실험: 확장 평가 · 실제 이미지 인스턴스 선택 · GrabCut 속도 · 동시 요청 부하 (+ `*.json` 원자료) |
