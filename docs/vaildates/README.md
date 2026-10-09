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
| [gif-matte-20261009.md](./gif-matte-20261009.md) | GIF 경계 매트: 올릴 배경색과 미리 섞으면 경계 오차 2.6~3.6배 감소, 반대 배경이면 악화 → 작업실에서 선택(기본 정하지 않음) |
| [video-removal-20261009.md](./video-removal-20261009.md) | 영상 · GIF 지우기: 다른 프레임에서 보인 배경판으로 메우기 — 움직이는 대상 L1 26.4→0 · 깜빡임 22.5→0, 제자리 대상 27.3→23.8, 카메라 이동은 자동으로 예전 방식. LaMa 입력 테두리 누수 수정 |
| [inpaint-20261009.md](./inpaint-20261009.md) | 대상 지우기 빈자리 메우기 Telea → LaMa(ONNX): 정답 있는 구멍 60개, L1 20.2→16.2 · PSNR +2.3dB · 무늬(경사) 오차 −25%, LaMa 가 나은 비율 77~98% (10-09 재측정), 사진 1장 +1.3초 |
| [ui-design-20261008.md](./ui-design-20261008.md) | 사용자 앱 디자인 고도화(다크 유지): Pretendard · 한국어 줄바꿈 · 공통 디자인 클래스 · 홈 원본/결과 데모 · 작업실 단계 · 모바일 펼침 메뉴, 화면 18개 가로 스크롤·오류 0건 |
| [lora-retrain-20261008.md](./lora-retrain-20261008.md) | LoRA 재학습(방해물 문장 180 시드): 방해물 문장 대상 78.7→95.7%, 홀드아웃 70.0→87.5%, 처음 본 30문장 70.0→73.3% — 판정 통과해 배포본 교체, 기본 LLM 은 ollama+체인 유지(96.7%) |
| [leak-diagnosis-20261008.md](./leak-diagnosis-20261008.md) | 지정하지 않은 인물·동물·물체가 대상에 섞이는 문제: 정답 주석으로 섞임을 재는 도구, 100+개 라운드(가설 검증·레시피·모델·신호·문장 해석), 원인 4곳과 수정 (섞임 6.3→4.1%, 경계 F 0.52→0.61), 효과 없던 것 기록 |
| [stuff-segmentation-20261008.md](./stuff-segmentation-20261008.md) | 건물·하늘·도로 같은 배경 덩어리 인식: 학습 없이 SegFormer(ADE20K, ONNX) 추가, b0/b2/b5 비교(ADE20K 100장, 건물 IoU 0.85~0.86), Docker 요청 확인, 큰 영역 지우기 한계 |
| [edge-tuning-20261008.md](./edge-tuning-20261008.md) | 경계·영상 흔들림 튜닝: GrabCut 2번→1번(경계 F +25%, 시간 절반), 경계 안티앨리어싱, 흐름 보정 스무딩(흔들림 −50%) + `edge_quality_20261008.json` |
| [open-vocab-20261007.md](./open-vocab-20261007.md) | 오픈 보캐브(DINO+SAM2) 실가동 + 박스 임계값 측정(COCO 3,000쌍: 0.25→0.35 오검출 17.9%→7.4%, 재현율 −3.9%p) + `open_vocab_threshold_20261007.json` |
| [experiments-20261006.md](./experiments-20261006.md) | 실험: 확장 평가 · 실제 이미지 인스턴스 선택 · GrabCut 속도 · 동시 요청 부하 (+ `*.json` 원자료) |
