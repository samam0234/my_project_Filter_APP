# 스프레드시트

기준 파일은 로컬 Scribble의 CutNKeep_프로젝트_관련_스프레드시트_문서_2026-10-11.xlsx 이다. 그 파일은 저장소에 올라가지 않으므로, 같은 내용을 Portfolio/assets/spreadsheet.json 으로 옮겨 두었다.

시트 기준은 2026-10-11, develop 4468283 이다. 그 다음 날 인수인계에서 확인된 변화는 시트 숫자와 다르다.

- 실서버는 진행 중이 아니라 공개 운영 중이다. 주소는 https://168-110-17-193.sslip.io 와 Cloudflare Worker cutnkeep-front 이다.
- 가입은 이메일 일련번호 인증이 추가되었다. 대기 테이블은 signup_pending 이며, 이 시트의 테이블 명세서에는 없다.
- 프롬프트 가이드에 AI 채팅(에이전트에게 묻기, POST /api/v1/chat)이 있다. 대화는 서버에 저장하지 않는다.
- 테스트 수는 시트 기록(백엔드 463, 프론트 65, 콘솔 21)보다 뒤의 인수인계 수치인 백엔드 505, 프론트 95, 콘솔 21을 따른다.

## 시트 목록

1. 프로젝트_총기획 (60행)
2. 기능_설계 (63행)
3. 용어_정리 (65행)
4. 테이블_명세서 (95행)
5. 스키마_설계 (45행)
6. URL_설계 (82행)
7. 화면_설계 (32행)
8. 간트_차트 (26행)
9. 향후_계획 (40행)
10. 변경_이력 (14행)

## 프로젝트_총기획

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 프로젝트 총기획  \|  목적·범위·기술 스택·배포 요약 (출처: README · docs/plan/CURRENT_STACK.md · docs/FEATURES.md, 기준 develop 4468283 (2026-10-11)) |   |
| --- | --- |
| 항목 | 내용 |
| 1. 프로젝트 개요 |   |
| 프로젝트명 | 컷앤킵 (Cut & Keep, CutNKeep) |
| 한 줄 설명 | 자연어 문장으로 원하는 대상만 남기거나(배경 제거·블러·크롭) 필요 없는 대상을 지우는 지능형 필터 웹 앱 — 사진 · 움직이는 GIF · 짧은 영상 · 배치 지원 |
| 개발 형태 | 1인 개발 (대학생 / BiNCS AI·Data Engineer 훈련생), AI 코딩 도우미(Claude·Grok 등) 병행 |
| 저장소 | https://github.com/samam0234/my_project_Filter_APP (기본 브랜치 develop, 작업 feature/* → develop/main merge --no-ff) |
| 로컬 경로 | D:\vscode\CutAndKeep\my_project_Filter_APP |
| 개발 기간 (실제) | 2026-07-27 첫 커밋 → 2026-10-11 현재 (11주, 커밋 395건). 집중 개발 구간: 09-29 ~ 10-11 |
| 현재 상태 | Phase 1·2·3 코드 구현 완료 (README Phase 표 ✅). 남은 것: 실서버(OCI)·도메인 배포와 점검, 운영 데이터가 쌓이면 세그·LoRA 재학습 |
| 테스트 | 백엔드 pytest 463 · 프론트 vitest 65 · 콘솔 vitest 21 통과 (2026-10-10, docs/plan/TESTING.md), CI: pytest + pip-audit + npm audit + preflight |
| 2. 제작 목적 (Why Cut & Keep?) |   |
| 문제 | AI 학습 데이터 준비 시 수천~수만 장 이미지에 bbox를 수작업으로 그려야 하며, 사각형 bbox는 물체의 실제 실루엣을 반영하지 못함 |
| 해결 | 자연어 문장(예: '강아지만 남기고 배경 제거', '맨 앞 빨간 안전모 쓴 사람만', '오른쪽 사람 지워줘')으로 대상을 지정하면 픽셀 단위 마스크로 해당 객체만 추출하거나 지움 |
| 기대 효과 | 라벨링 수작업·비용 절감, 정밀한 객체 단위 데이터 확보, 사용자 교정(정답 알려주기) → 검수 → RAG·LoRA 재학습으로 지속 개선 |
| 대상 사용자 | AI 연구자·개발자, 소규모 팀, 이미지·영상 편집/합성이 필요한 일반 사용자 (비로그인도 처리·다운로드 가능) |
| 3. 핵심 기능 (현재 코드 기준) |   |
| 사진 처리 | 업로드 → 문장 → 처리. 남기고 배경 제거(투명 PNG) · 배경 블러(강도) · 크롭 · 대상 지우기(LaMa 인페인팅) |
| 특정 대상 고르기 | 위치 · 순서 · 개수 · 크기 · 색/부위 선택자(selector) — '왼쪽에서 두 번째 사람', '사람 2명', '가장 큰 개' |
| 배경 덩어리 | 건물 · 하늘 · 도로 · 나무 등 14종 (SegFormer ADE20K ONNX) |
| GIF | 프레임마다 처리, 투명 GIF(매트: 밝은/어두운 배경) + 부드러운 경계 WebP, 최대 120프레임 |
| 영상 | 최대 20초 · 80MB · 긴 변 3840, H.264 mp4 + 오디오, 광학 흐름 스무딩, 고른 대상 프레임 간 추적, 다른 프레임 배경판으로 지우기 |
| 해석 모델 고르기 | 작업실 처리하기 옆 상자: Ollama gemma4:e4b(기본) · gemma4:12b · qwen3.8:27b, 서버에 없는 모델은 '미적용' |
| 배치 (회원) | 같은 문장으로 최대 500장, 진행률, 실패 항목 표시, 결과 zip 다운로드 (Celery 선택) |
| 회원 · 작업 기록 | 회원가입(만 14세·약관·처리방침 동의) · 로그인 · 아이디/비밀번호 찾기 · 내 계정(정보·보안·탈퇴) · 작업 기록(사진·영상·GIF) |
| 학습 루프 | 좋아요/싫어요 · 정답 알려주기 → 학습 DB → 운영 콘솔 검수 → RAG 즉시 반영 · LoRA/YOLO 재학습 스크립트 |
| 운영 콘솔 | 별도 앱(:5174): 대시보드 · 작업 · 배치 · 학습 데이터 검수 · 회원 관리 · 시스템 점검/정리 |
| 4. 기술 스택 |   |
| Frontend | React 18 + TypeScript 5 + Vite 7 + Tailwind CSS 3 + Zustand 4, 자체 경량 라우터(router.tsx), Vitest 5 · Pretendard 글꼴 |
| Console | React + Vite 7 + Tailwind (console/, :5174, Compose 미포함) |
| Backend | FastAPI 0.143 · Starlette 1.7 · Pydantic 2 · Uvicorn (Python 3.10~3.12), 계층: routers · schemas · services · repositories · models(ORM) · db |
| DB | 서비스 DB: MariaDB 11 (Docker) / SQLite (호스트 개발) · 학습 DB: MariaDB (꺼져 있으면 SQLite fallback) · SQLAlchemy 2 |
| 이미지 처리 | OpenCV (전처리, 마스크 겹침 덜어내기, 업스케일·안티앨리어싱·깃털 알파 경계, Telea 인페인팅 fallback) |
| 세그멘테이션 | YOLO26m-seg (.pt / ONNX 직접 추론) + SegFormer ADE20K ONNX(배경 덩어리) + Grounding DINO + SAM2(오픈 보캐브, 기본 꺼짐) |
| 지우기 | LaMa ONNX 인페인팅(사진), 배경판(시간 중앙값 + 밝기 맞춤, 영상·GIF), Telea fallback |
| 문장 해석 | LangChain 해석 체인(LLM + 키워드 파서 다수결) · Ollama gemma4:e4b 기본 · LoRA(Qwen2.5-1.5B 어댑터, GPU) · OpenAI/Gemini 선택 · RAG(TF-IDF) 예시 |
| 워크플로우 | LangGraph 1.2 + langchain-core 1.6 (스레드풀 실행, 재시도 시 조건 변경 + 최선 시도 채택, 모델 워밍업) |
| 배치/큐 | Celery 5 + Redis 7 (프로필 phase2, BATCH_USE_CELERY=true일 때만) |
| 학습 | training/ (YOLO detect/seg, LoRA), scripts/retrain_lora.py · retrain_yolo.py · seg_labeling.py · pseudo_labeling.py |
| 배포 | Docker Compose(-p cut_and_keep): frontend(nginx :80) · backend · MariaDB · Redis · Adminer · mariadb-backup (+ https 오버레이 Caddy 80/443, + gpu 오버레이), 프런트는 Cloudflare Worker로도 배포 |
| CI | GitHub Actions: pytest · pip-audit · preflight · 프론트/콘솔 npm test · build · npm audit |
| 5. 성공 기준 (MVP) 달성 현황 |   |
| 정확도 | 목표 80% → 문장 해석: Ollama 체인 처음 본 문장 96.7%, LoRA 283문장 94.7% · 대상 선택: '왼쪽 사람' 90.0% · 영상 추적(실제 DAVIS) 92.1% (docs/vaildates) |
| 피드백 | 달성 — 학습 DB(feedbacks · learning_samples) + data/feedback 사이드카, 콘솔 검수 |
| 배치 안정성 | 구현 — 최대 500장, 한 장씩 처리·실패 항목 표시·zip. 실서버 500장 부하 측정은 배포 후 확인 필요 |
| 6. 보안 · 운영 정책 |   |
| 접근 정책 | 비로그인: 처리·다운로드만(서버 저장 없음, IP별 분당 6회) / 회원: 저장·기록·피드백·배치(본인 것만, 분당 20회) / 콘솔: 관리자 로그인(CONSOLE_ADMINS) |
| 업로드 검증 | 확장자 · MIME · 시그니처 · 해상도(압축 폭탄) — 사진 jpg/png/webp ≤20MB, 영상 ≤80MB, GIF ≤4MP |
| 계정 보안 | scrypt 해시, 5회 실패 잠금, HttpOnly 세션 쿠키(7일), 이메일 6자리 코드 재설정 |
| 보관 | 회원 업로드 24시간 후 자동 삭제(60분마다), 실패 사진 30일, 계정 삭제 시 즉시 · MariaDB 매일 백업 7일 보관 |
| 배포 보안 | 공개 포트는 80/443만, 내부(backend·DB·Redis·Adminer)는 127.0.0.1 바인딩, CSP 등 보안 헤더, production 위험 기본값이면 기동 거부(preflight) |
| 7. 배포 환경 (Oracle Cloud, 2026-10-10 결정) |   |
| 클라우드 | Oracle Cloud Infrastructure (OCI) — Always Free 범위 |
| 인스턴스 | cutnkeep-server · VM.Standard.A1.Flex (Ampere ARM) 4 OCPU / 24 GB · Canonical Ubuntu 24.04 aarch64 · 부트 볼륨 100 GB |
| 네트워크 (VCN) | 새 VCN 생성(마법사: 인터넷 연결) cutnkeep-vcn 10.0.0.0/16 · 공용 서브넷 10.0.0.0/24 · 전용 서브넷 10.0.1.0/24 |
| 보안 목록 (수신) | TCP 22(SSH) · 80(HTTP) · 443(HTTPS)만 허용. 8000(backend) · 3306/3309(MariaDB) · 6379/6380(Redis) · 8081(Adminer)은 열지 않음 |
| 서비스 구성 | docker compose -f docker-compose.yml -f docker-compose.https.yml (Caddy 자동 인증서 → nginx → backend). 운영 .env 는 scripts/make_prod_env.py, 모델은 scripts/models_bundle.py 로 이전 |
| 프런트 경로 | Cloudflare Worker(cutnkeep-front) 정적 화면 + /api 프록시 → ORIGIN https://168-110-17-193.sslip.io (레포 wrangler.jsonc 값 = 서버 공인 IP 기반 임시 도메인) |
| 주의 | ARM(aarch64) CPU 서버 → GPU 오버레이·LoRA 해석 불가, Ollama 큰 모델(27b)은 메모리 부족으로 '미적용'이 정상. DINO+SAM2 는 CPU로 느림 → GPU 셰이프나 외부 API 검토 |

## 기능_설계

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 기능 설계  \|  기능 목록·담당 모듈·단계·구현 상태 (상태는 develop 4468283 (2026-10-11) 코드 확인, 초록 칸 = 07-27 이후 신규) |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 기능 ID | 분류 | 기능명 | 상세 설명 | 관련 모듈 / 파일 | Phase | 우선순위 | 구현 상태 |
| F-01 | 업로드 | 이미지 업로드 | 드래그앤드롭/파일 선택, 미리보기 (작업실 1단계) | ImageUploader.tsx / POST /api/v1/upload | 1 | 상 | 구현 |
| F-02 | 보안 | 업로드 파일 검증 | 확장자·MIME·시그니처·해상도(압축 폭탄) 검사, 사진 jpg/png/webp ≤20MB | core/security.py | 1 | 상 | 구현 |
| F-03 | 프롬프트 | 문장 입력 | 문장 1~1000자, 예시 문장 칩, 해석 결과 칩 표시 | PromptInput.tsx · ExamplePrompts.tsx · ParsedPromptView.tsx | 1 | 상 | 구현 |
| F-04 | 프롬프트 | 문장 해석 (LLM) | LLM → {target, effect, intensity, crop, selector} JSON. 기본 Ollama gemma4:e4b, lora/openai/gemini 선택, 실패 시 키워드 파서 | services/prompt_llm.py · prompt_spec.py | 1 | 상 | 구현 |
| F-05 | 프롬프트 | 키워드 파서 | LLM 없이도 동작하는 어휘 확장 + 역할 규칙(남길 것·뺄 것·지울 것) 파서 (대상 56.6→100%) | services/heuristic_targets.py | 1 | 상 | 구현 |
| F-06 | 프롬프트 | 해석 체인 (LangChain) | LLM 답과 키워드 파서가 다르면 최대 3번 물어 다수결 (처음 본 문장 86.7→96.7%) | services/prompt_chain.py (PROMPT_CHAIN) | 2 | 상 | 구현 |
| F-07 | 프롬프트 | 프롬프트 RAG | 승인된 사용자 교정·좋아요 중 비슷한 문장을 LLM 예시로 (TF-IDF, 30초 안에 반영) | services/prompt_rag.py (PROMPT_RAG_*) | 2 | 중 | 구현 |
| F-08 | 프롬프트 | 해석 모델 고르기 | 작업실 처리하기 옆 상자에서 Ollama e4b·12b·Qwen 3.8 27b 선택, 미설치 모델은 '미적용' | ModelSelect.tsx · services/llm_models.py · GET /api/v1/llm/models | 3 | 중 | 구현 |
| F-09 | 프롬프트 | LoRA 해석 모델 | Qwen2.5-1.5B 어댑터 (283문장 94.7%, GPU 1.0초/문장), GPU 오버레이 기본, 혼합 모드(PROMPT_SECOND_OPINION) | services/prompt_lora.py · training/lora/ | 2 | 중 | 구현 |
| F-10 | 전처리 | 이미지 전처리 | 종횡비 유지 resize, CLAHE(현재 기본 끔), 색공간 변환 | services/image_processor.py | 1 | 상 | 구현 |
| F-11 | 세그멘테이션 | 객체 세그멘테이션 | YOLO26m-seg (.pt 또는 ONNX 직접 추론), COCO 80종 + 한국어 별칭 | services/segmentation.py · utils/onnx_utils.py | 1 | 상 | 구현 |
| F-12 | 세그멘테이션 | 배경 덩어리 세그 | SegFormer ADE20K ONNX로 건물·하늘·도로 등 14종 | services/stuff_segmentation.py | 2 | 중 | 구현 |
| F-13 | 세그멘테이션 | 오픈 보캐브 세그 | Grounding DINO + SAM2 (박스 임계값 0.35), 기본 꺼짐·로컬 가중치 필요 | segmentation.py (OPEN_VOCAB_*) | 2 | 중 | 선택(기본 꺼짐) |
| F-14 | 세그멘테이션 | 특정 인스턴스 고르기 | 위치·순서·개수·크기·색/부위로 같은 클래스 중 특정 대상 선택 ('왼쪽 사람' 90.0%) | services/instance_selector.py | 1 | 상 | 구현 |
| F-15 | 세그멘테이션 | 섞임 막기 | 다른 인스턴스 몫 덜어내기(MASK_EXCLUSIVE=subtract), GrabCut·CLAHE 끔 (섞임 6.3→4.1%) | services/mask_exclusion.py | 1 | 상 | 구현 |
| F-16 | 검증 | 마스크 품질 검증 · 재시도 | ok/fallback/failed 판정, 반대쪽 입력 + 낮은 신뢰도로 재시도 후 더 나은 시도 채택 | services/validator.py · workflows/edges.py | 1 | 상 | 구현 |
| F-17 | 효과 | 배경 제거 | 업스케일·안티앨리어싱·깃털 알파 경계 → 투명 PNG | services/effects.py | 1 | 상 | 구현 |
| F-18 | 효과 | 배경 블러 | 대상 외 영역 블러, 강도(0~100), 영상은 해상도 보정 | services/effects.py | 1 | 중 | 구현 |
| F-19 | 효과 | 대상 크롭 | 대상 주변으로 자름 | services/effects.py | 1 | 중 | 구현 |
| F-20 | 효과 | 대상 지우기 (사진) | LaMa ONNX 인페인팅으로 주변 무늬를 이어 그림, 모델 없으면 Telea (L1 20.2→16.2) | services/inpaint.py · model_fetch.py | 2 | 상 | 구현 |
| F-21 | 결과 | 원본/결과 비교 | 손잡이 끌기 비교, 투명 배경 체커보드, PNG/JPEG 저장 | BeforeAfterViewer.tsx · ResultImage.tsx | 1 | 상 | 구현 |
| F-22 | 결과 | 처리 상태 표시 | 진행 막대(해석·대상 찾기·효과), 상태 배지, 품질 점수 | ProcessingStatus.tsx · StatusBadge.tsx | 1 | 중 | 구현 |
| F-23 | 피드백 | 평가 · 정답 알려주기 | 좋아요/싫어요 + 해석이 틀리면 올바른 값을 골라 전송 → 검수 후 학습 | FeedbackPanel.tsx · POST /api/v1/feedback | 1 | 상 | 구현 |
| F-24 | 피드백 | 실패·어려운 사례 수집 | 파이프라인 실패 이미지 + 메타 자동 저장, 확신 낮은 성공 사례(HARD_EXAMPLE_CONF, 기본 끔) | workflows/nodes.py feedback_collector | 1 | 중 | 구현 |
| F-25 | GIF | GIF 처리 | 프레임마다 처리, 간격·반복 유지, 투명 GIF(매트) + 부드러운 경계 WebP, 120프레임 | GifWorkspace.tsx · services/gif_processor.py · POST /api/v1/gif | 2 | 중 | 구현 |
| F-26 | 영상 | 영상 처리 | 20초·80MB·긴 변 3840, H.264 mp4 + 오디오, 결과를 브라우저(IndexedDB)에 보관 | VideoPage.tsx · services/video_processor.py · POST/GET /api/v1/video | 2 | 중 | 구현 |
| F-27 | 영상 | 흔들림 보정 | 광학 흐름 스무딩 (흔들림 −50%) | services/video_processor.py | 3 | 중 | 구현 |
| F-28 | 영상 | 고른 대상 추적 | 첫 프레임에 고른 대상을 끝까지 유지 (실제 영상 DAVIS 72.8→92.1%) | services/instance_tracker.py (VIDEO_TRACK_INSTANCES) | 3 | 중 | 구현 |
| F-29 | 영상 | 영상·GIF 지우기 | 다른 프레임에서 보인 배경판으로 메움(고정·이동 카메라 프레임 맞춤), 안 맞으면 Telea | services/video_inpaint.py (VIDEO_REMOVE_MODE) | 3 | 중 | 구현 |
| F-30 | 배치 | 배치 처리 (회원) | 같은 문장으로 최대 500장, 진행률 자동 갱신, 실패 항목 표시, 항목 원본/결과 | BatchPage.tsx · routers/batch.py · tasks/batch_tasks.py | 2 | 상 | 구현 |
| F-31 | 배치 | 배치 결과 zip | 배치 결과 전체 zip 다운로드 | GET /api/v1/batch/{id}/download | 2 | 중 | 구현 |
| F-32 | 계정 | 회원가입 | 규칙 즉시 안내, [필수] 만 14세·약관·처리방침 동의(서버 검사, 동의 시각 기록) | SignupPage.tsx · POST /api/v1/auth/signup | 1 | 상 | 구현 |
| F-33 | 계정 | 로그인 · 로그아웃 | HttpOnly 세션 쿠키, ?next= 복귀, 5회 실패 잠금 | LoginPage.tsx · /api/v1/auth/login · logout · me | 1 | 상 | 구현 |
| F-34 | 계정 | 아이디 · 비밀번호 찾기 | 가입 이메일로 아이디 발송, 이메일 6자리 코드 → 새 비밀번호 | FindIdPage.tsx · FindPasswordPage.tsx · /auth/find-id · /auth/password/* | 1 | 중 | 구현 |
| F-35 | 계정 | 내 계정 | 프로필 메뉴 → 내 정보(표시 이름·이용 현황) · 작업 기록 · 보안(비밀번호 변경·모든 기기 로그아웃) · 탈퇴 | AccountPage.tsx · PATCH/DELETE /auth/me · /auth/password/change · /auth/logout-all | 3 | 중 | 구현 |
| F-36 | 계정 | 작업 기록 · 상세 | 사진·영상·GIF 모아 보기(종류·상태 필터·검색), 다시 받기, 같은 문장으로 다시 작업 | HistoryPanel.tsx · JobDetailPage.tsx · GET /api/v1/jobs | 1 | 중 | 구현 |
| F-37 | 안내 | 프롬프트 가이드 · 법적 고지 | 남기기/지우기·선택자 예시·한계, 개인정보 처리방침·이용약관(실제 동작과 같은 보관 기간) | GuidePage.tsx · PrivacyPage.tsx · TermsPage.tsx | 3 | 중 | 구현 |
| F-38 | 운영 | 운영 콘솔 | 관리자 로그인, 대시보드·작업·배치·학습 데이터 검수·회원 관리·시스템 점검/정리 | console/ · routers/console.py | 2 | 상 | 구현 |
| F-39 | 학습 | 학습 데이터 카탈로그 · 검수 | 피드백/요청에서 학습 후보 생성 → 콘솔 승인·정답 고쳐 승인·거절·일괄, train/val 고정 분할 | services/learning_catalog.py · learning_review.py | 2 | 상 | 구현 |
| F-40 | 학습 | LoRA 재학습 | 증강·학습·평가셋 7개 판정·배포(--deploy), 조합형 시드 | scripts/retrain_lora.py · training/lora/ | 2 | 중 | 구현 |
| F-41 | 학습 | 세그 재학습 · 라벨링 | 실패 사진 초벌 라벨 → Label Studio → 검사, 이어 학습·섞임/mAP 판정·배포 | scripts/seg_labeling.py · retrain_yolo.py | 2 | 중 | 구현 |
| F-42 | 학습 | Pseudo Labeling · 모델 평가 | 오픈 보캐브로 라벨 후보, 검증셋 평가 | scripts/pseudo_labeling.py · evaluate_model.py | 2 | 중 | 구현 |
| F-43 | 운영 | 파일 자동 정리 | 회원 업로드 24시간 후 60분마다 삭제(.gitkeep 보호), 실패 사진 30일 | services/retention.py · feedback_images.py | 1 | 중 | 구현 |
| F-44 | 운영 | DB 백업 · 손상 감지 | MariaDB 매일 덤프 7일 보관(복구 확인), SQLite 온라인 백업, 기동 시 quick_check | mariadb-backup 서비스 · services/db_backup.py | 2 | 중 | 구현 |
| F-45 | 보안 | 속도 제한 · 보안 헤더 | 비로그인 IP별 6회/분 · 회원 20회/분, CSP·X-Frame-Options 등, 내부 포트 127.0.0.1 | core/ratelimit.py · frontend/nginx.conf | 3 | 상 | 구현 |
| F-46 | 운영 | Docker 배포 | frontend(nginx) · backend · MariaDB · Redis · Adminer · backup, celery_worker(phase2) | docker-compose.yml · backend/Dockerfile | 3 | 상 | 구현 |
| F-47 | 운영 | HTTPS · 메일 | Caddy 자동 인증서·HSTS, SMTP 587/465, 개발용 Mailpit | docker-compose.https.yml · services/mailer.py | 3 | 상 | 구현 |
| F-48 | 운영 | GPU 오버레이 | CUDA torch(cu128/cu130) 이미지, LoRA 해석 · 세그 GPU | docker-compose.gpu.yml | 3 | 중 | 구현 |
| F-49 | 운영 | 배포 도구 | 운영 .env 생성(make_prod_env), 배포 점검(deploy_check), 모델 묶음/체크섬(models_bundle), 기동 전 점검(preflight) | scripts/ · core/preflight.py | 3 | 상 | 구현 |
| F-50 | 운영 | Cloudflare 프런트 | Worker가 정적 화면 + /api·/health 프록시, EDGE_SECRET으로 실제 사용자 IP 전달 | deploy/cloudflare/ | 3 | 중 | 구현 |
| F-51 | 운영 | 실서버 배포 (OCI) | A1.Flex Ubuntu 24.04 · 새 VCN · 22/80/443, HTTPS 오버레이, 도메인·점검 | docs/DEPLOYMENT.md (서버 작업) | 3 | 상 | 진행 중 |
| F-52 | 기능 | 라벨 포맷 내보내기 | 마스크를 COCO / YOLO-seg 폴리곤으로 내보내기 (사용자 기능) | (신규) | - | 중 | 예정 |
| F-53 | 기능 | 브라우저 로컬 추론 | ONNX Runtime Web / WebGPU로 서버 전송 없이 처리 | (신규) | - | 하 | 예정 |
| 요약 |   |   |   |   |   |   |   |
| 구현 |   |   |   |   |   |   |   |
| 선택(기본 꺼짐) |   |   |   |   |   |   |   |
| 진행 중 |   |   |   |   |   |   |   |
| 예정 |   |   |   |   |   |   |   |
| 합계 |   |   |   |   |   |   |   |
| 07-27판 대비: 스텁이던 배치·Pseudo Labeling·LoRA·평가는 구현으로, 예정이던 오픈 보캐브·영상·Temporal Smoothing은 구현으로 바뀜. 계정·콘솔·GIF·지우기·추적·배포 도구 등 28개 기능 신규(초록 칸). |   |   |   |   |   |   |   |

## 용어_정리

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 용어 정리  \|  프로젝트에서 사용하는 AI·이미지 처리·개발·배포 용어 (초록 칸 = 신규 용어) |   |   |   |
| --- | --- | --- | --- |
| 용어 | 분류 | 설명 | 예시 / 코드 위치 |
| 프롬프트 (문장) | AI | 사용자가 자연어로 입력하는 처리 명령 | '왼쪽 사람만 남기고 배경 블러' |
| ParsedPrompt | AI | 문장을 구조화한 JSON (target, effect, intensity, crop, selector) | {"target":["person"],"effect":"remove_bg"} |
| effect | AI | 효과 종류: remove_bg(남기고 배경 제거) · blur · crop · remove_object(지우기) · none | services/prompt_spec.py |
| selector (선택자) | AI | 같은 클래스 중 특정 대상을 고르는 조건: position · rank · count · attributes(색/부위) | InstanceSelector, instance_selector.py |
| 세그멘테이션 | AI | 이미지에서 객체 영역을 픽셀 단위로 분리하는 작업 | YOLO-seg 마스크 |
| 마스크 (Mask) | AI | 대상 픽셀=255, 배경=0 인 이진 이미지 | mask.png |
| bbox | AI | 객체를 감싸는 사각형. 실루엣을 반영 못하는 한계가 프로젝트 동기 | (x, y, w, h) |
| YOLO26m-seg | AI | 현재 서빙 세그 모델 (Ultralytics YOLO26 medium, 인스턴스 세그). 07-27판의 YOLOv8n-seg 를 대체 | backend/models/yolo26m-seg.pt / .onnx |
| ONNX / ONNX Runtime | AI | 모델 표준 포맷 / 추론 엔진. SEG_RUNTIME=onnx 이면 torch 없이 슬림 이미지(약 1.1GB) | utils/onnx_utils.py |
| SegFormer (ADE20K) | AI | 건물·하늘·도로 등 '배경 덩어리(stuff)'를 인식하는 시맨틱 세그 모델 | services/stuff_segmentation.py |
| Grounding DINO + SAM2 | AI | 텍스트로 대상을 탐지(DINO)하고 정밀 마스크(SAM2)를 만드는 오픈 보캐브 조합. 기본 꺼짐 | OPEN_VOCAB_* |
| 오픈 보캐브 | AI | 학습 클래스 밖의 자유 문구 대상도 찾는 방식 | '빨간 가방' |
| LaMa | AI | 학습형 인페인팅 모델. 지운 자리를 주변 무늬로 이어 그림 | backend/models/lama_fp32.onnx |
| 인페인팅 / Telea | OpenCV | 빈 영역 메우기 / OpenCV 고전 인페인팅 (LaMa 없을 때 fallback) | services/inpaint.py |
| 배경판 | AI | 영상·GIF에서 다른 프레임에 보인 실제 배경을 시간 중앙값으로 합친 판. 지우기에 사용 | services/video_inpaint.py |
| 인스턴스 추적 | AI | 첫 프레임에 고른 대상을 프레임 사이로 따라가는 기능 | services/instance_tracker.py |
| 광학 흐름 (Optical Flow) | AI | 프레임 간 움직임 추정. 마스크 흔들림 보정에 사용 | video_processor.py |
| 매트 (matte) | 이미지 | 1비트 투명 GIF 경계를 올릴 배경색(밝은/어두운)과 미리 섞어 부드럽게 하는 처리 | POST /gif matte=light\|dark |
| 섞임 (leak) | AI | 지정하지 않은 인물·물체가 결과 마스크에 섞여 들어가는 문제 | mask_exclusion.py, MASK_EXCLUSIVE |
| LLM | AI | 문장 해석용 대형 언어 모델. 기본 Ollama gemma4:e4b | services/prompt_llm.py |
| Ollama | AI | 로컬 LLM 서버. gemma4:e4b · gemma4:12b · qwen3.8:27b | LLM_BASE_URL :11434 |
| 키워드 파서 | AI | LLM 없이 어휘·역할 규칙으로 문장을 해석하는 파서 | heuristic_targets.py |
| 해석 체인 | AI | LangChain으로 LLM 답과 키워드 파서를 비교해 다수결로 확정 | prompt_chain.py, PROMPT_CHAIN |
| RAG | AI | Retrieval-Augmented Generation. 승인된 비슷한 문장을 LLM 예시로 붙임 | prompt_rag.py |
| LoRA | AI | Low-Rank Adaptation, 소수 파라미터만 추가 학습. 현재는 문장 해석(Qwen2.5-1.5B) 어댑터에 사용 | training/lora/, retrain_lora.py |
| Pseudo Labeling | AI | 모델이 만든 라벨을 학습 후보로 쓰는 반자동 라벨링 | scripts/pseudo_labeling.py |
| 학습 샘플 (learning_sample) | AI | 학습에 쓸 수 있는 데이터 1건 (kind=prompt\|segment, status=pending→approved/rejected) | 학습 DB learning_samples |
| train / val split | AI | 승인 시 id 해시로 고정 배정되는 학습/검증 구분 (val 10%) | learning_samples.split |
| mIoU / mAP | AI | 세그 정확도 지표 / 탐지·세그 평균 정밀도 | evaluate_model.py, retrain_yolo.py |
| DAVIS 2017 | AI | 실제 영상 세그 벤치마크. 추적·지우기 검증에 사용 | docs/vaildates/davis-real-video-20261010.md |
| GrabCut / CLAHE | OpenCV | 경계 정제 / 대비 향상 알고리즘. 섞임 문제로 현재 기본 끔 | MASK_GRABCUT, PREPROCESS_CLAHE |
| 알파 채널 | OpenCV | 투명도 채널. 배경 제거 결과를 투명 PNG/WebP로 저장 | after.png |
| LangGraph | Backend | 상태·노드·엣지 기반 워크플로우 (1.2) | workflows/graph.py |
| GraphState | Backend | 노드 간 공유 상태 (job_id, prompt, llm_model, parsed_prompt, selection, attempts, timings 등) | workflows/state.py |
| Fallback | Backend | 세그멘테이션이 불충분할 때 최선 결과로 처리 완료하는 상태 | status=fallback |
| job / kind | Backend | 처리 작업 1건 / 작업 종류 image · video · gif | jobs.kind |
| 서비스 DB / 학습 DB | Backend | 회원·작업·배치 DB / 피드백·학습 샘플 DB (분리 운영, 서로 FK 없음) | db/session.py, db/learning.py |
| MariaDB | Backend | Docker 운영 DB (공식 mariadb:11, 비밀번호 전용, skip_ssl) | docker/mariadb/ |
| SQLite | Backend | 호스트 개발용 서비스 DB 및 학습 DB fallback | backend/data/cutnkeep.host.db |
| Repository | Backend | DB 접근 계층 (job·batch·feedback·user) | app/repositories/ |
| Celery / Redis | Backend | 선택형 비동기 배치 워커 / 브로커 (프로필 phase2) | redis://redis:6379/0 |
| scrypt / HttpOnly 세션 | 보안 | 비밀번호 해시 알고리즘 / JS에서 읽을 수 없는 로그인 쿠키 | core/passwords.py, auth_service.py |
| preflight | 보안 | production 환경에서 위험한 기본값이면 기동을 거부하는 점검 | core/preflight.py |
| Rate Limit | 보안 | 요청 수 제한 (비로그인 6회/분, 회원 20회/분) | core/ratelimit.py |
| FastAPI | Backend | Python 비동기 웹 프레임워크 (0.143), /docs 자동 문서 | app/main.py |
| Zustand | Frontend | React 경량 전역 상태 관리 (앱·인증·해석 모델 스토어) | store/useAppStore.ts 등 |
| 작업실 (Studio) | Frontend | 사진·GIF 처리 화면 (1 사진 → 2 문장 → 3 처리) | /studio |
| 운영 콘솔 | Frontend | 관리자용 별도 웹 앱 (:5174) | console/ |
| IndexedDB | Frontend | 브라우저 내장 DB. 영상 마지막 결과 보관 | utils/videoStore.ts |
| Docker Compose | 배포 | 여러 컨테이너 묶음 실행. 프로젝트 이름 cut_and_keep | docker-compose.yml |
| 오버레이 (https · gpu) | 배포 | 기본 compose 위에 겹쳐 쓰는 추가 설정 파일 | docker-compose.https.yml, docker-compose.gpu.yml |
| Caddy | 배포 | 자동 HTTPS 인증서 발급·갱신 리버스 프록시 (80/443) | docker/caddy/Caddyfile |
| nginx | 배포 | frontend 정적 파일 서빙 + /api 를 backend:8000 으로 프록시 | frontend/nginx.conf |
| Cloudflare Worker | 배포 | Cloudflare 에서 정적 화면을 주고 /api 를 서버로 넘기는 엣지 함수 | deploy/cloudflare/worker.js |
| EDGE_SECRET | 배포 | Worker 가 넘긴 실제 사용자 IP 헤더를 Caddy 가 믿게 하는 공유 비밀 값 | set_edge_secret.sh |
| sslip.io | 배포 | IP 주소를 그대로 도메인으로 쓰게 해 주는 무료 DNS (임시 HTTPS용) | 168-110-17-193.sslip.io |
| OCI | 배포 | Oracle Cloud Infrastructure. 배포 대상 클라우드 | Always Free |
| A1.Flex (Ampere) | 배포 | OCI ARM(aarch64) 가상 머신 셰이프. 4 OCPU / 24 GB 무료 | VM.Standard.A1.Flex |
| VCN / 서브넷 | 배포 | OCI 가상 클라우드 네트워크 / 그 안의 IP 대역 (공용 10.0.0.0/24, 전용 10.0.1.0/24) | cutnkeep-vcn 10.0.0.0/16 |
| 보안 목록 (Security List) | 배포 | OCI 서브넷 방화벽 규칙. 수신 22/80/443만 허용 | OCI 콘솔 > 네트워킹 |
| Phase | 기획 | 개발 단계 (1: MVP, 2: 혁신성 강화, 3: 고도화·배포) — 현재 1~3 코드 완료 | README Phase 표 |
| MVP | 기획 | Minimum Viable Product, 최소 기능 제품 | docs/vaildates/mvp-checklist.md |

## 테이블_명세서

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 테이블 명세서  \|  실제 ORM(backend/app/models) 기준 컬럼 명세 — 서비스 DB 5개 + 학습 DB 2개 (develop 4468283 (2026-10-11)) |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
| 테이블명 | 컬럼명 | 데이터 타입 | PK/FK | NULL | 기본값 | 설명 |
| ※ 07-27판의 'Phase 2 PostgreSQL 설계안'(parsed_prompts · pseudo_labels · model_versions 포함)을 실제 구현으로 교체. DB: Docker = MariaDB 11, 호스트 개발 = SQLite. 서비스 DB와 학습 DB는 분리되어 서로 FK 없음(값으로만 참조). |   |   |   |   |   |   |
| [서비스 DB] users  (회원 계정) |   |   |   |   |   |   |
| users | id | VARCHAR(32) | PK | N | uuid4().hex | 회원 ID |
| users | username | VARCHAR(32) | UQ, IDX | N |   | 아이디 (소문자 정규화, 대소문자 무시 유일) |
| users | email | VARCHAR(255) | UQ, IDX | N |   | 이메일 (유일) |
| users | display_name | VARCHAR(50) |   | Y | NULL | 표시 이름 |
| users | password_hash | VARCHAR(255) |   | N |   | scrypt 해시 (원문 저장 없음) |
| users | failed_logins | INTEGER |   | N | 0 | 연속 로그인 실패 수 |
| users | locked_until | DATETIME(tz) |   | Y | NULL | 잠금 해제 시각 (LOGIN_LOCK_MINUTES) |
| users | last_login_at | DATETIME(tz) |   | Y | NULL | 마지막 로그인 |
| users | terms_agreed_at | DATETIME(tz) |   | Y | NULL | 만 14세·약관·처리방침 동의 시각 (예전 회원 NULL) |
| users | created_at | DATETIME(tz) |   | N | now() | 가입 시각 |
| users | updated_at | DATETIME(tz) |   | N | now() / on update | 수정 시각 |
| [서비스 DB] auth_sessions  (로그인 세션) |   |   |   |   |   |   |
| auth_sessions | id | VARCHAR(64) | PK | N |   | 세션 토큰 SHA-256 (토큰 원문은 쿠키에만) |
| auth_sessions | user_id | VARCHAR(32) | FK → users.id (CASCADE), IDX | N |   | 회원 |
| auth_sessions | expires_at | DATETIME(tz) |   | N |   | 만료 (SESSION_TTL_HOURS=168) |
| auth_sessions | user_agent | VARCHAR(255) |   | Y | NULL | 접속 브라우저 |
| auth_sessions | created_at | DATETIME(tz) |   | N | now() | 생성 시각 |
| [서비스 DB] auth_codes  (비밀번호 재설정 코드) |   |   |   |   |   |   |
| auth_codes | id | INTEGER | PK (auto) | N | autoincrement | 코드 ID |
| auth_codes | user_id | VARCHAR(32) | FK → users.id (CASCADE), IDX | N |   | 회원 |
| auth_codes | purpose | VARCHAR(32) |   | N |   | password_reset |
| auth_codes | code_hash | VARCHAR(64) |   | N |   | 6자리 코드 HMAC-SHA256 |
| auth_codes | attempts | INTEGER |   | N | 0 | 입력 시도 수 |
| auth_codes | expires_at | DATETIME(tz) |   | N |   | 만료 시각 |
| auth_codes | used_at | DATETIME(tz) |   | Y | NULL | 사용 시각 (1회용) |
| auth_codes | created_at | DATETIME(tz) |   | N | now() | 생성 시각 |
| [서비스 DB] jobs  (처리 작업: 사진 · 영상 · GIF) |   |   |   |   |   |   |
| jobs | id | VARCHAR(64) | PK | N | uuid hex | job_id (API 노출 값과 동일) |
| jobs | user_id | VARCHAR(32) | FK → users.id (SET NULL), IDX | Y | NULL | 소유 회원 (비로그인 작업은 저장 안 함, 탈퇴 시 NULL) |
| jobs | prompt | TEXT |   | N |   | 원본 문장 |
| jobs | kind | VARCHAR(16) |   | Y | 'image' | image \| video \| gif (NULL인 예전 행 = image) |
| jobs | status | VARCHAR(32) | IDX | N |   | pending \| ok \| fallback \| failed |
| jobs | parsed_prompt | JSON |   | Y | NULL | ParsedPrompt (target, effect, intensity, crop, selector) — 07-27판의 parsed_prompts 테이블을 흡수 |
| jobs | quality_score | FLOAT |   | N | 0.0 | 검증 점수 (0~1) |
| jobs | before_path | VARCHAR(512) |   | Y | NULL | 원본 경로 (사진 before.jpg · GIF before.gif · 영상 in.*) |
| jobs | after_path | VARCHAR(512) |   | Y | NULL | 결과 경로 (after.png\|jpg · after.gif(+webp) · result.mp4) |
| jobs | backend | VARCHAR(64) |   | Y | NULL | 세그 백엔드 (yolo \| stub 등) |
| jobs | message | TEXT |   | Y | NULL | 처리 메시지 |
| jobs | labels | JSON |   | Y | NULL | 검출 라벨 목록 |
| jobs | confidences | JSON |   | Y | NULL | 검출 신뢰도 목록 |
| jobs | feedback_saved | INTEGER |   | N | 0 | 피드백 존재 여부 0/1 |
| jobs | error | TEXT |   | Y | NULL | 오류 내용 |
| jobs | created_at | DATETIME(tz) |   | N | now() | 생성 시각 |
| jobs | updated_at | DATETIME(tz) |   | N | now() / on update | 수정 시각 |
| jobs | expires_at | DATETIME(tz) |   | Y | NULL | 파일 만료 (FILE_RETENTION_HOURS=24) |
| [서비스 DB] batch_jobs  (배치 작업, 회원 전용) |   |   |   |   |   |   |
| batch_jobs | id | VARCHAR(64) | PK | N | uuid hex | 배치 ID |
| batch_jobs | user_id | VARCHAR(32) | FK → users.id (SET NULL), IDX | Y | NULL | 등록 회원 |
| batch_jobs | status | VARCHAR(32) |   | N | 'pending' | pending \| running \| done \| failed |
| batch_jobs | prompt | TEXT |   | N | '' | 배치 공통 문장 (기본 폼값 'person remove background') |
| batch_jobs | total | INTEGER |   | N | 0 | 전체 파일 수 (≤500) |
| batch_jobs | completed | INTEGER |   | N | 0 | 완료 수 |
| batch_jobs | progress | FLOAT |   | N | 0.0 | 진행률 0.0~1.0 |
| batch_jobs | message | TEXT |   | Y | NULL | 메시지 |
| batch_jobs | item_results | JSON |   | Y | NULL | 항목별 결과 스냅샷 목록 |
| batch_jobs | created_at | DATETIME(tz) |   | N | now() | 생성 시각 |
| batch_jobs | updated_at | DATETIME(tz) |   | N | now() / on update | 수정 시각 |
| [학습 DB] feedbacks  (피드백 이벤트 원장) |   |   |   |   |   |   |
| feedbacks | id | VARCHAR(64) | PK | N |   | case_id = data/feedback/{id}.json 사이드카 파일명 |
| feedbacks | job_id | VARCHAR(64) | IDX (값 참조, FK 없음) | N |   | 서비스 DB jobs.id |
| feedbacks | user_id | VARCHAR(32) | IDX (값 참조, FK 없음) | Y | NULL | 서비스 DB users.id |
| feedbacks | vote | VARCHAR(16) |   | N |   | like \| dislike |
| feedbacks | comment | TEXT |   | Y | NULL | 코멘트 (정답 JSON이면 교정) |
| feedbacks | source | VARCHAR(32) | IDX | N | 'user' | user \| pipeline_failure |
| feedbacks | prompt | TEXT |   | Y | NULL | 요청 문장 (job에서 보강) |
| feedbacks | image_path | VARCHAR(512) |   | Y | NULL | 실패 원본 이미지 (저장소 루트 기준 상대 경로) |
| feedbacks | meta | JSON |   | Y | NULL | parsed_prompt, 점수 등 |
| feedbacks | created_at | DATETIME(tz) |   | N | now() | 피드백 시각 |
| [학습 DB] learning_samples  (학습 데이터 카탈로그) |   |   |   |   |   |   |
| learning_samples | id | VARCHAR(32) | PK | N | uuid4().hex | 샘플 ID |
| learning_samples | kind | VARCHAR(16) | IDX, UQ(origin_id+kind) | N |   | prompt (문장→정답, LoRA·RAG) \| segment (세그 실패 이미지) |
| learning_samples | source | VARCHAR(32) | IDX | N |   | correction \| like \| request \| pipeline_failure \| pseudo_label |
| learning_samples | status | VARCHAR(16) | IDX | N | 'pending' | pending → approved \| rejected (콘솔 검수) · deleted |
| learning_samples | split | VARCHAR(8) | IDX | Y | NULL | train \| val (승인 시 id 해시로 고정) |
| learning_samples | origin_id | VARCHAR(64) | IDX, UQ(origin_id+kind) | N |   | 출처 레코드 (feedbacks.id 또는 의사 라벨 case_id) |
| learning_samples | job_id | VARCHAR(64) | IDX | Y | NULL | 관련 작업 |
| learning_samples | user_id | VARCHAR(32) | IDX | Y | NULL | 관련 회원 |
| learning_samples | prompt | TEXT |   | Y | NULL | 문장 |
| learning_samples | answer | JSON |   | Y | NULL | ParsedPrompt 정답 |
| learning_samples | image_path | VARCHAR(512) |   | Y | NULL | 이미지 경로 |
| learning_samples | label_path | VARCHAR(512) |   | Y | NULL | 사이드카 JSON 경로 |
| learning_samples | note | TEXT |   | Y | NULL | 검수 메모 |
| learning_samples | reviewed_by | VARCHAR(64) |   | Y | NULL | 검수자 |
| learning_samples | reviewed_at | DATETIME(tz) |   | Y | NULL | 검수 시각 |
| learning_samples | created_at | DATETIME(tz) |   | N | now() | 생성 시각 |
| learning_samples | updated_at | DATETIME(tz) |   | N | now() / on update | 수정 시각 |
| 07-27 설계안에서 제거된 테이블 |   |   |   |   |   |   |
| parsed_prompts | - | - | - | - | - | jobs.parsed_prompt(JSON) 컬럼으로 대체 |
| pseudo_labels | - | - | - | - | - | learning_samples(source=pseudo_label)로 대체 |
| model_versions | - | - | - | - | - | DB 테이블 없음 — 모델은 backend/models/ 파일, 판정·배포는 retrain_* 스크립트 + docs/vaildates 기록 |

## 스키마_설계

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 스키마 설계  \|  DB 관계·API·워크플로우·파일 저장 스키마 (실제 코드 기준) |   |   |   |   |
| --- | --- | --- | --- | --- |
| 구분 | 이름 | 필드 / 정의 | 타입·제약 | 관계 / 비고 |
| A. 데이터베이스 관계 (ERD: cutnkeep/erd/cutnkeep_erd_2026-10-11.*) |   |   |   |   |
| 관계 | users ─< auth_sessions | users.id = auth_sessions.user_id | 1 : N, ON DELETE CASCADE | 로그인 세션 |
| 관계 | users ─< auth_codes | users.id = auth_codes.user_id | 1 : N, ON DELETE CASCADE | 비밀번호 재설정 코드 |
| 관계 | users ─< jobs | users.id = jobs.user_id | 1 : N (선택), ON DELETE SET NULL | 비로그인 작업은 저장 안 함 |
| 관계 | users ─< batch_jobs | users.id = batch_jobs.user_id | 1 : N (선택), ON DELETE SET NULL | 배치는 회원 전용 |
| 논리 참조 | jobs ┄< feedbacks | jobs.id ↔ feedbacks.job_id | 1 : N, FK 없음 (DB가 다름) | 학습 DB는 값으로만 참조 |
| 논리 참조 | users ┄< feedbacks / learning_samples | users.id ↔ *.user_id | FK 없음 | 계정 삭제 시 실패 사진 즉시 삭제, 기록은 익명 |
| 논리 참조 | feedbacks ┄< learning_samples | feedbacks.id ↔ learning_samples.origin_id | 1 : 0~2 | 피드백 1건에서 prompt·segment 샘플 파생 |
| 유일 | uq_learning_samples_origin_kind | learning_samples(origin_id, kind) | UNIQUE | 같은 출처를 두 번 적재하지 않음 |
| 인덱스 | users | username · email | UNIQUE + INDEX | 로그인·찾기 |
| 인덱스 | jobs | user_id · status | INDEX | 작업 기록·콘솔 조회 |
| 인덱스 | learning_samples | kind · source · status · split · origin_id · job_id · user_id | INDEX | 콘솔 검수 필터 |
| B. API 스키마 (Pydantic, backend/app/schemas) |   |   |   |   |
| Request | UploadForm (multipart) | file, prompt, llm_model? | prompt 1~1000자, jpg/png/webp ≤20MB | POST /api/v1/upload |
| Model | ParsedPrompt | target: List[str], effect, intensity, crop, selector? | intensity 0~100, effect ∈ remove_bg\|blur\|crop\|remove_object\|none | schemas/request.py |
| Model | InstanceSelector | position?, rank?, count?, attributes[] | rank·count 1~50 | schemas/request.py |
| Response | UploadResponse | job_id, status, parsed_prompt?, before_url?, after_url?, quality_score, message?, feedback_saved, saved | 비로그인은 saved=false, 결과는 data URL | schemas/response.py |
| Response | JobResponse | job_id, prompt, status, parsed_prompt, quality_score, before/after/thumb/webp_url, backend, message, feedback_saved, created_at, kind | kind ∈ image\|video\|gif | GET /jobs, /jobs/{id} |
| Response | GifResponse | job_id, status, parsed_prompt, before/after_url, frames, total, held, effect, transparent, matte, message, saved | matte ∈ none\|light\|dark | POST /gif |
| Request | FeedbackRequest | job_id, vote(like\|dislike), comment? | comment ≤2000자 | POST /feedback |
| Response | FeedbackResponse | ok, job_id, feedback_id?, saved_path?, message |   | schemas/feedback.py |
| Request | Signup / Login / FindId / PasswordReset* | username, email, password, display_name?, agree_terms / code, new_password | username ≤64, password ≤128, code ≤12 | schemas/auth.py |
| Request | ProfileUpdate / PasswordChange / AccountDelete | display_name / current_password, new_password / password, confirm |   | PATCH·DELETE /auth/me, /auth/password/change |
| Response | UserResponse / MessageResponse | id, username, email, display_name, created_at / ok, message |   | schemas/auth.py |
| Console | LearningSampleResponse · ReviewRequest · BulkReviewRequest | 검수 대상 · action(approve\|reject\|reset) + answer?/note? · ids(≤500) |   | /console/learning/* |
| Response | HealthResponse | status, version, phase, db_dialect?, learning_db? | version 0.1.0, phase 1(상수) | GET /health |
| C. LangGraph 상태 스키마 (GraphState) |   |   |   |   |
| State | 식별/입력 | job_id, image_bytes, image_path, prompt, llm_model | TypedDict(total=False) | workflows/state.py |
| State | 해석 | parsed_prompt, prompt_parser, prompt_rag | 어떤 해석기·RAG 예시를 썼는지 보존 |   |
| State | 세그/검증 | status, error, quality_score, confidences, labels, detected, selection, leak, backend, segment_strategy, attempts, chosen_attempt | 재시도마다 조건 변경, 최선 시도 채택 |   |
| State | 산출물/제어 | before_path, after_path, feedback_saved, feedback_meta, retry_count, persist, timings, message | persist=false면 저장 안 함(비로그인) |   |
| Flow | 노드 순서 | prompt_analyzer → preprocessor → segmentor → validator → (increment_retry ↺ segmentor \| feedback_collector) → effect_applier → END | 스레드풀 실행 | workflows/graph.py |
| Flow | 조건부 분기 | after_validator: effect_applier \| retry_segmentor \| feedback_then_effects | 실패해도 효과는 best-effort | workflows/edges.py |
| Flow | 영상·GIF | 프레임마다 같은 규칙(FrameRenderer) + instance_tracker + video_inpaint |   | services/video_processor.py · gif_processor.py |
| D. 파일 저장 스키마 |   |   |   |   |
| Storage | backend/data/uploads/{job_id}/ | before.jpg · after.png\|jpg · thumb · (GIF) before.gif · after.gif · after.webp | 회원만, 24시간 후 자동 삭제 | UPLOAD_DIR (런타임) |
| Storage | backend/data/uploads/videos/{job_id}/ | in.* · result.mp4 · thumb.jpg · original.mp4(avi 등 미리 보기) | 회원만, 24시간 |   |
| Storage | data/feedback/{case_id}.json (+ .jpg) | case_id, job_id, vote, comment, meta, 실패 원본 사진 | 실패 사진 30일 보관 | 학습 공유 (루트) |
| Storage | data/pseudo_labels/ | 의사 라벨 마스크 |   | 학습 공유 |
| Storage | backend/models/ | yolo26m-seg.pt/.onnx, SegFormer ONNX, lama_fp32.onnx, LoRA 어댑터 | git 밖 — models_bundle 로 이전 | 서빙 가중치 |
| Storage | data/mariaDB_datas/ · data/mariaDB_backups/ | MariaDB 데이터 · 매일 덤프 *.sql.gz | 7일 보관 | bind mount |
| Storage | backend/logs/app_YYYY-MM-DD.log | 런타임 로그 | 14일 | LOG_DIR |

## URL_설계

CutNKeep 프로젝트 관련 스프레드 시트 문서

| URL 설계  \|  API 엔드포인트 · 사용자 화면 · 콘솔 · 배포 주소 (routers/*.py, frontend/src/App.tsx 기준) |   |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| No | 구분 | Method | URL | 설명 | Request | Response / 권한 | Phase | 상태 |
| Backend API (FastAPI, Base: http://localhost:8000, Prefix: /api/v1) — 🔒 회원 전용 · 🛠 콘솔 관리자 |   |   |   |   |   |   |   |   |
| 1 | System | GET | /health | 서버 상태 · DB 종류 | - | HealthResponse | 1 | 구현 |
| 2 | Docs | GET | /docs | Swagger UI (production 비노출) | - | HTML | 1 | 구현 |
| 3 | Upload | POST | /api/v1/upload | 사진 업로드 + 파이프라인 실행 | multipart: file, prompt, llm_model? | UploadResponse | 1 | 구현 |
| 4 | Upload | GET | /api/v1/files/{job_id}/before | 원본 이미지 | path: job_id | image 🔒 본인만 | 1 | 구현 |
| 5 | Upload | GET | /api/v1/files/{job_id}/after | 결과 이미지 (영상은 mp4) | path: job_id | image/video 🔒 | 1 | 구현 |
| 6 | Upload | GET | /api/v1/files/{job_id}/webp | GIF 부드러운 경계 WebP | path: job_id | image/webp 🔒 | 2 | 구현 |
| 7 | Upload | GET | /api/v1/files/{job_id}/thumb | 썸네일 (영상·GIF) | path: job_id | image/jpeg 🔒 | 2 | 구현 |
| 8 | GIF | POST | /api/v1/gif | 움직이는 GIF 처리 | multipart: file, prompt, matte, llm_model? | GifResponse | 2 | 구현 |
| 9 | Video | POST | /api/v1/video | 영상 업로드 + 프레임별 처리 | multipart: file, prompt, llm_model? | job_id, status, result | 2 | 구현 |
| 10 | Video | GET | /api/v1/video/{job_id} | 영상 결과 조회 | path: job_id | status, result_url 🔒 | 2 | 구현 |
| 11 | LLM | GET | /api/v1/llm/models | 해석 모델 목록 · 설치 여부 | - | models[] (미적용 표시) | 3 | 구현 |
| 12 | Feedback | POST | /api/v1/feedback | 좋아요/싫어요 · 정답 알려주기 | JSON: FeedbackRequest | FeedbackResponse 🔒 | 1 | 구현 |
| 13 | Jobs | GET | /api/v1/jobs | 내 작업 기록 (?limit, 종류·상태) | query | JobResponse[] 🔒 | 1 | 구현 |
| 14 | Jobs | GET | /api/v1/jobs/{job_id} | 작업 상세 | path: job_id | JobResponse 🔒 | 1 | 구현 |
| 15 | Batch | POST | /api/v1/batch | 배치 등록 (최대 500장) | multipart: files[], prompt | batch status 🔒 | 2 | 구현 |
| 16 | Batch | GET | /api/v1/batch | 내 배치 목록 | - | list 🔒 | 2 | 구현 |
| 17 | Batch | GET | /api/v1/batch/{job_id} | 배치 진행률 | path | status, progress 🔒 | 2 | 구현 |
| 18 | Batch | GET | /api/v1/batch/{job_id}/items/{index}/{kind} | 배치 항목 원본/결과 | kind: before\|after | image 🔒 | 2 | 구현 |
| 19 | Batch | GET | /api/v1/batch/{job_id}/download | 배치 결과 zip | path | application/zip 🔒 | 2 | 구현 |
| 20 | Auth | POST | /api/v1/auth/signup | 회원가입 (동의 필수) | JSON: SignupRequest | UserResponse (201) | 1 | 구현 |
| 21 | Auth | POST | /api/v1/auth/login | 로그인 (세션 쿠키 발급) | JSON: LoginRequest | UserResponse | 1 | 구현 |
| 22 | Auth | POST | /api/v1/auth/logout | 로그아웃 | - | MessageResponse | 1 | 구현 |
| 23 | Auth | GET | /api/v1/auth/me | 현재 로그인 정보 | - | UserResponse 🔒 | 1 | 구현 |
| 24 | Auth | PATCH | /api/v1/auth/me | 표시 이름 수정 | JSON: ProfileUpdate | UserResponse 🔒 | 3 | 구현 |
| 25 | Auth | DELETE | /api/v1/auth/me | 계정 탈퇴 (파일 포함 삭제) | JSON: AccountDelete | MessageResponse 🔒 | 3 | 구현 |
| 26 | Auth | POST | /api/v1/auth/find-id | 아이디 찾기 (메일 발송) | JSON: email | MessageResponse | 1 | 구현 |
| 27 | Auth | POST | /api/v1/auth/password/request | 재설정 코드 요청 | JSON: username, email | MessageResponse | 1 | 구현 |
| 28 | Auth | POST | /api/v1/auth/password/reset | 코드로 새 비밀번호 | JSON: username, code, new_password | MessageResponse | 1 | 구현 |
| 29 | Auth | POST | /api/v1/auth/password/change | 비밀번호 변경 | JSON: PasswordChange | MessageResponse 🔒 | 3 | 구현 |
| 30 | Auth | POST | /api/v1/auth/logout-all | 모든 기기 로그아웃 | - | MessageResponse 🔒 | 3 | 구현 |
| 31 | Console | GET | /api/v1/console/me | 콘솔 관리자 확인 | - | 🛠 | 2 | 구현 |
| 32 | Console | GET | /api/v1/console/jobs · /jobs/{job_id} | 전체 작업 조회 | query/path | JobResponse 🛠 | 2 | 구현 |
| 33 | Console | GET | /api/v1/console/batches | 전체 회원 배치 (이미지 비노출) | - | 🛠 | 2 | 구현 |
| 34 | Console | GET | /api/v1/console/files/{job_id}/{kind} | 작업 파일 | path | image 🛠 | 2 | 구현 |
| 35 | Console | GET | /api/v1/console/learning/stats | 학습 데이터 통계 | - | 🛠 | 2 | 구현 |
| 36 | Console | GET | /api/v1/console/learning/samples | 학습 샘플 목록 | query | LearningSampleList 🛠 | 2 | 구현 |
| 37 | Console | POST | /api/v1/console/learning/samples/{id}/review | 검수 (승인·거절·초기화) | JSON: ReviewRequest | 🛠 | 2 | 구현 |
| 38 | Console | POST | /api/v1/console/learning/samples/bulk | 일괄 검수 | JSON: BulkReviewRequest | BulkReviewResponse 🛠 | 2 | 구현 |
| 39 | Console | DELETE | /api/v1/console/learning/samples/{id} | 샘플 삭제 (deleted 표식) | path | DeleteResponse 🛠 | 2 | 구현 |
| 40 | Console | GET | /api/v1/console/learning/samples/{id}/image | 샘플 원본 이미지 | path | image 🛠 | 2 | 구현 |
| 41 | Console | GET | /api/v1/console/users | 회원 검색 | query | 🛠 | 2 | 구현 |
| 42 | Console | POST | /api/v1/console/users/{id}/unlock | 잠금 해제 | path | 🛠 | 2 | 구현 |
| 43 | Console | POST | /api/v1/console/users/{id}/sessions/revoke | 세션 끊기 | path | 🛠 | 2 | 구현 |
| 44 | Console | DELETE | /api/v1/console/users/{id} | 회원 삭제 (파일 포함) | path | 🛠 | 2 | 구현 |
| 45 | Console | GET | /api/v1/console/system | 설정 점검 · 런타임 · 저장 공간 | - | 🛠 | 2 | 구현 |
| 46 | Console | POST | /api/v1/console/system/cleanup | 보관 기간 정리 실행 | - | 🛠 | 2 | 구현 |
| 사용자 화면 (React + Vite, http://localhost:5173 / Docker nginx :80 / Cloudflare Worker) |   |   |   |   |   |   |   |   |
| 47 | Page | - | / | 홈 (비교 데모 · 예시 문장 · 최근 작업) | - | - | 1 | 구현 |
| 48 | Page | - | /studio | 작업실 — 사진 처리 | - | - | 1 | 구현 |
| 49 | Page | - | /studio?type=gif | 작업실 — GIF 처리 | - | - | 2 | 구현 |
| 50 | Page | - | /video | 영상 처리 | - | - | 2 | 구현 |
| 51 | Page | - | /batch | 배치 🔒 | - | - | 2 | 구현 |
| 52 | Page | - | /account | 내 계정 🔒 (정보 · 기록 · 보안 · 탈퇴) | - | - | 3 | 구현 |
| 53 | Page | - | /account?tab=history | 작업 기록 🔒 (/history 는 여기로 이동) | - | - | 1 | 구현 |
| 54 | Page | - | /jobs/:id | 작업 상세 🔒 | - | - | 1 | 구현 |
| 55 | Page | - | /guide | 프롬프트 가이드 | - | - | 3 | 구현 |
| 56 | Page | - | /login | 로그인 | - | - | 1 | 구현 |
| 57 | Page | - | /signup | 회원가입 | - | - | 1 | 구현 |
| 58 | Page | - | /find-id | 아이디 찾기 | - | - | 1 | 구현 |
| 59 | Page | - | /find-password | 비밀번호 찾기 | - | - | 1 | 구현 |
| 60 | Page | - | /privacy | 개인정보 처리방침 | - | - | 3 | 구현 |
| 61 | Page | - | /terms | 이용약관 | - | - | 3 | 구현 |
| 운영 콘솔 (console/, http://localhost:5174 — Compose 미포함, 관리자 PC에서 실행) |   |   |   |   |   |   |   |   |
| 62 | Console | - | (메뉴) 로그인 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 63 | Console | - | (메뉴) 대시보드 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 64 | Console | - | (메뉴) 작업 목록 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 65 | Console | - | (메뉴) 배치 현황 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 66 | Console | - | (메뉴) 학습 데이터 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 67 | Console | - | (메뉴) 회원 관리 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 68 | Console | - | (메뉴) 시스템 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 69 | Console | - | (메뉴) 바로가기 | 콘솔 내부 화면 (상단 /api/v1/console/* 사용) | - | 관리자 | 2 | 구현 |
| 배포 주소 · 포트 |   |   |   |   |   |   |   |   |
| 70 | Edge | - | https://cutnkeep-front.<계정>.workers.dev | Cloudflare Worker: 정적 화면 + /api/* · /health 프록시 | - | - | 3 | 구현 |
| 71 | Origin | - | https://168-110-17-193.sslip.io | OCI 서버 (Caddy :443 → nginx → backend). wrangler.jsonc ORIGIN 값 | - | - | 3 | 진행 중 |
| 72 | Port | - | :22 / :80 / :443 | OCI 보안 목록에서 여는 유일한 수신 포트 (SSH · HTTP · HTTPS) | - | - | 3 | 진행 중 |
| 73 | Port | - | 127.0.0.1:8000 · :3309 · :6380 · :8081 | backend · MariaDB · Redis · Adminer — 서버 내부 전용 (보안 목록에서 닫음) | - | - | 3 | 구현 |
| 74 | 예정 | - | https://<자체 도메인> | 도메인 구입 후 A 레코드 → ORIGIN 교체 | - | - | 3 | 예정 |
| 07-27판 대비: 예정이던 /api/v1/models/active 는 만들지 않음(모델은 파일·스크립트로 관리), /api/v1/video/{id} 는 구현. 계정 11개·콘솔 18개·GIF·LLM·Jobs·배치 항목 API 신규. 화면은 /batch·/video 구현, /about 대신 /guide. |   |   |   |   |   |   |   |   |

## 화면_설계

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 화면 설계  \|  화면 구성·컴포넌트·이벤트 (frontend/src · console/src 기준) |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
| 화면 ID | 화면명 | URL | 구성 요소 (컴포넌트) | 주요 동작 / 이벤트 | 호출 API | Phase |
| 사용자 앱 |   |   |   |   |   |   |
| S-01 | 공통 레이아웃 | 전 화면 | AppLayout: 로고·메뉴(1024px 미만 펼침 메뉴)·서버 상태 점·프로필 메뉴·푸터 | 30초마다 /health, 로그인 시 프로필 메뉴(내 계정·로그아웃) | GET /health · /auth/me | 1 |
| S-02 | 홈 | / | HeroDemo(배경 제거·지우기·블러 탭 비교 슬라이더), 예시 문장, 사용 순서, 최근 작업(JobCard) | 예시 문장 클릭 → 작업실로 이동, 손잡이 끌기·←/→ | GET /jobs?limit=4 | 1 |
| S-03 | 작업실 — 사진 | /studio | Step 1~3, ImageUploader, PromptInput + ExamplePrompts, ModelSelect, ProcessingStatus, ParsedPromptView, BeforeAfterViewer, FeedbackPanel | 처리하기 → 진행 막대(해석·대상 찾기·효과) → 결과 비교 → PNG/JPEG 저장 → 평가·정답 알려주기 | POST /upload · GET /llm/models · POST /feedback | 1 |
| S-04 | 작업실 — GIF | /studio?type=gif | GifWorkspace: GIF 업로드, 문장, 매트(밝은/어두운) 선택, 결과 GIF/WebP | 프레임 수·간격 유지, 투명 GIF + WebP 다운로드 | POST /gif | 2 |
| S-05 | 영상 | /video | 영상 업로드(20초·80MB), 문장, ModelSelect, 진행, 결과 플레이어 | 결과를 IndexedDB 보관, 문장 고쳐 다시 처리, mp4 다운로드 | POST /video · GET /video/{id} | 2 |
| S-06 | 배치 🔒 | /batch | 다중 파일 선택(최대 500), 문장, 진행률 바, 항목 그리드(원본/결과·실패 표시) | 진행률 자동 갱신, 결과 zip 다운로드 | POST/GET /batch · items · download | 2 |
| S-07 | 내 계정 🔒 | /account | 탭: 내 정보(표시 이름·이용 현황) · 작업 기록(HistoryPanel) · 보안 · 보관 안내/탈퇴 | 이름 수정, 비밀번호 변경, 모든 기기 로그아웃, 탈퇴 확인 | PATCH/DELETE /auth/me · /auth/password/change · /auth/logout-all · GET /jobs | 3 |
| S-08 | 작업 상세 🔒 | /jobs/:id | 결과 다시 보기(영상 재생), 해석 JSON 복사, FeedbackPanel | 같은 문장으로 다시 작업 | GET /jobs/{id} · /files/{id}/* | 1 |
| S-09 | 프롬프트 가이드 | /guide | 남기기 vs 지우기, 선택자 예시, 한계, 보관 안내 | 예시 클릭 → 작업실 | - | 3 |
| S-10 | 로그인 | /login | AuthForm: 아이디·비밀번호 | ?next= 로 돌아가기, 잠금 안내 | POST /auth/login | 1 |
| S-11 | 회원가입 | /signup | AuthForm + 필수 동의 3종(만 14세·약관·처리방침), 보관·학습 이용 안내 | 입력 즉시 규칙 안내 | POST /auth/signup | 1 |
| S-12 | 아이디·비밀번호 찾기 | /find-id · /find-password | 이메일 입력 / 아이디·이메일 → 코드 → 새 비밀번호 | 있든 없든 같은 안내 | POST /auth/find-id · /auth/password/* | 1 |
| S-13 | 법적 고지 | /privacy · /terms | 개인정보 처리방침 · 이용약관 (운영자 정보는 빌드 인자) | - | - | 3 |
| S-14 | 페이지 없음 | (기타) | NotFoundPage | 홈으로 | - | 1 |
| 운영 콘솔 |   |   |   |   |   |   |
| C-01 | 콘솔 로그인 | (console) | LoginPage | 관리자 계정 확인 | GET /console/me | 2 |
| C-02 | 대시보드 | (console) | StatCard 집계, 최근 작업 | 상태·집계 | GET /health · /console/jobs | 2 |
| C-03 | 작업 · 배치 | (console) | JobsPage · BatchesPage | 사진·영상·GIF 구분, 배치 현황 | /console/jobs · /console/batches | 2 |
| C-04 | 학습 데이터 | (console) | LearningPage: 필터·통계·원본 이미지 | 승인 · 정답 고쳐 승인 · 거절 · 일괄 | /console/learning/* | 2 |
| C-05 | 회원 관리 | (console) | UsersPage | 검색·잠금 해제·세션 끊기·삭제 | /console/users* | 2 |
| C-06 | 시스템 | (console) | SystemPage: 설정 점검·런타임·엔진·저장 공간 | 보관 기간 정리 실행 | /console/system · /system/cleanup | 2 |
| 화면 흐름 |   |   |   |   |   |   |
| FLOW | 기본 사용자 흐름 | /studio | S-03 사진 → 문장 → (모델 선택) → 처리 → 결과 비교 → 저장 → 평가 | 비로그인: 저장 없이 다운로드만 · 회원: 작업 기록에 남음 |   | 1 |
| FLOW | 회원 흐름 | /signup → /account | S-11 가입 → S-10 로그인 → S-07 내 계정/작업 기록 → S-08 상세 |   |   | 1 |
| FLOW | 학습 흐름 | 작업실 → 콘솔 | 정답 알려주기 → C-04 검수 승인 → RAG 즉시 반영 / LoRA 재학습 |   |   | 2 |
| 공통 UI 규칙 |   |   |   |   |   |   |
| UI | 디자인 | - | 다크 테마, Pretendard, 낱말 단위 줄바꿈, 키보드 초점 링, 모바일 펼침 메뉴 | docs/vaildates/ui-design-20261008.md |   | 1 |
| UI | 상태 관리 | - | Zustand: useAppStore(작업) · useAuthStore(로그인) · useLlmModelStore(해석 모델) | 자체 라우터 router.tsx (navigate · matchRoute) |   | 1 |

## 간트_차트

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 간트 차트  \|  실제 개발 일정(git 커밋 기준) + 남은 배포·운영 계획. 노란 칸(시작일·시작주·기간·진행률)을 수정하면 날짜와 막대가 자동 갱신됩니다. |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 프로젝트 시작일 |   | 46230 | 실제 첫 커밋 2026-07-27(월). W11 = 10-05~10-11(현재 주) |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| No | Phase | 작업명 | 시작주 | 기간(주) | 시작일 | 종료일 | 진행률 | W1 | W2 | W3 | W4 | W5 | W6 | W7 | W8 | W9 | W10 | W11 | W12 | W13 | W14 | W15 | W16 |
| 주 시작일 → |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 1 | Phase 1 | 개발 환경·저장소·Docker(MariaDB·Adminer)·YOLO26 세그 기본 | 1 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 2 | Phase 1 | YOLO 학습 데이터(COCO 5k)·학습 환경·LoRA 학습 본선 | 3 | 6 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 3 | Phase 1 | LLM 문장 해석·특정 인스턴스 선택·물체 지우기 | 10 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 4 | Phase 1 | 회원 계정·접근 정책·사용자 앱 6페이지·정답 알려주기 | 10 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 5 | Phase 1 | LangGraph 파이프라인 고도화·RAG | 10 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 6 | Phase 2 | 운영 콘솔 (검수·회원·시스템) | 10 | 2 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 7 | Phase 2 | 서비스/학습 DB 분리·MariaDB 전환·자동 백업 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 8 | Phase 2 | 배치 500장·영상·오픈 보캐브(DINO+SAM2)·ONNX 슬림 이미지 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 9 | Phase 2 | 해석 체인·키워드 파서·LoRA 재학습 루프 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 10 | Phase 2 | SegFormer 배경 덩어리·섞임 막기·LaMa 지우기 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 11 | Phase 3 | GIF·영상 추적·배경판 지우기·DAVIS 실제 영상 검증 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 12 | Phase 3 | 보안·HTTPS·개인정보 처리방침·배포 도구·GPU 오버레이 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 13 | Phase 3 | 내 계정·해석 모델 고르기·Cloudflare Worker 프런트 | 11 | 1 |   |   | 1 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 14 | 배포 | OCI 인스턴스(A1.Flex)·새 VCN·보안 목록 22/80/443 구성 | 11 | 2 |   |   | 0.5 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 15 | 배포 | 실서버 HTTPS·도메인 연결·deploy_check 점검 | 12 | 1 |   |   | 0 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 16 | 운영 | 운영 데이터 누적 → 세그·LoRA 재학습, 성능 모니터링 | 12 | 4 |   |   | 0 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 17 | 마무리 | 문서화 + 발표 준비 | 14 | 2 |   |   | 0.3 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
|   |   | 전체 진행률 (기간 가중 평균) |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
|   |   | 프로젝트 종료 예정일 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 범례: 초록=완료(100%) / 주황=진행 중 / 파랑=예정 · 노란 칸=수정 가능 입력값 · 빨간 머리글=현재 주(W11) · 완료 작업은 git 커밋 날짜, 배포 진행률 50%는 레포의 Cloudflare ORIGIN·운영 장애 기록(10-11)으로 본 추정치 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |
| 참고: W3~W9(08월~09월 중순)는 커밋이 드문 구간(학습 데이터·LoRA 준비). 커밋 수 07-27~29: 99건, 09-29~10-11: 288건 |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |   |

## 향후_계획

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 향후 계획  \|  배포(OCI)·운영·개선 계획과 리스크 대응 (2026-10-11 기준, 07-27판 계획 중 완료 항목은 아래 '완료' 절로 이동) |   |   |   |   |   |   |
| --- | --- | --- | --- | --- | --- | --- |
| No | 구분 | 계획 항목 | 상세 내용 | 목표 시점 | 우선순위 | 기대 효과 |
| 단기 — 실서버 배포 (Oracle Cloud, W11~W12) |   |   |   |   |   |   |
| 1 | 인프라 | OCI 인스턴스 생성 | cutnkeep-server: VM.Standard.A1.Flex 4 OCPU / 24 GB (Always Free), Canonical Ubuntu 24.04 aarch64, 부트 볼륨 100 GB, SSH 키 로그인 | W11 | 상 | 무료 상시 서버 확보 |
| 2 | 인프라 | 새 VCN · 서브넷 | VCN 마법사(인터넷 연결)로 cutnkeep-vcn 10.0.0.0/16, 공용 10.0.0.0/24(인스턴스), 전용 10.0.1.0/24(예비) | W11 | 상 | 기존 네트워크와 분리 |
| 3 | 보안 | 보안 목록 22/80/443 | 수신은 TCP 22·80·443만. 8000·3306/3309·6379/6380·8081은 열지 않음. Ubuntu 이미지 안의 iptables 에도 80·443 허용 필요(OCI 기본 이미지는 22 외 차단 규칙이 있음 — 확인 필요) | W11 | 상 | 공개 표면 최소화 |
| 4 | 배포 | Docker 기동 (ARM) | Docker + Compose 설치 → git clone → models_bundle 로 모델 이전 → make_prod_env 로 .env → compose + https 오버레이. ARM CPU 이므로 SEG_RUNTIME=onnx(슬림) 우선 검토, GPU 오버레이·LoRA 해석은 사용 안 함 | W12 | 상 | 실서비스 가동 |
| 5 | 배포 | 도메인 · HTTPS | 현재 임시 168-110-17-193.sslip.io → 자체 도메인 A 레코드, Caddy 인증서 확인, wrangler.jsonc ORIGIN 교체 후 wrangler deploy | W12 | 상 | 정식 주소 · 신뢰성 |
| 6 | 점검 | 배포 점검 | deploy_check remote(인증서·헤더·CORS·401) / server(.env·모델 체크섬·백업·서비스), 비로그인 7번째 요청 429 확인, 영상·GIF 긴 요청이 Worker 를 거쳐 끊기는지 확인 | W12 | 상 | 공개 전 안전 확인 |
| 7 | AI | ARM CPU 성능 측정 | A1(ARM) 4코어에서 사진 1장·GIF·영상 처리 시간, Ollama gemma4:e4b 첫 호출 시간 측정. 느리면 외부 LLM(OpenAI/Gemini) 또는 키워드 파서+체인 조정 | W12 | 중 | 응답 시간 기준 확보 |
| 중기 — 운영 개선 (W12~W15) |   |   |   |   |   |   |
| 8 | AI | 세그 재학습 | 실패·싫어요 사진이 쌓이면 seg_labeling → Label Studio → retrain_yolo(섞임·mAP 판정) → 배포 | W13~15 | 중 | 실제 사용 사진에 맞춘 정확도 |
| 9 | AI | LoRA 운영 반영 | 승인 문장이 쌓이면 retrain_lora, GPU 서버를 쓰게 되면 LLM_PROVIDER=lora 기본 (283문장 94.7%) | W13~15 | 중 | 해석 정확도·속도 |
| 10 | AI | 움직이는 카메라 지우기 | DAVIS 30개 중 18개는 여전히 예전 방식 → 프레임 맞춤 개선 | W14 | 중 | 영상 지우기 품질 |
| 11 | 운영 | 모니터링 · 백업 확인 | 디스크·메모리·로그(14일)·MariaDB 백업 복구 리허설, 콘솔 시스템 화면 활용 | W13 | 중 | 장애 대응 |
| 12 | 보안 | 콘솔 공개 시 접근 제한 | 운영 콘솔을 밖에 올리려면 Cloudflare Access 등 접근 제한 먼저 | 필요 시 | 중 | 관리 기능 보호 |
| 13 | 백엔드 | DB 마이그레이션 도구 | Alembic 도입 (현재는 기동 시 create_all + ALTER) | W15 | 하 | 스키마 변경 안전성 |
| 장기 — 확장 |   |   |   |   |   |   |
| 14 | 인프라 | GPU 처리 | 오픈 보캐브(DINO+SAM2)·LoRA 해석·큰 LLM 은 GPU 필요 → OCI GPU 셰이프 또는 외부 GPU/추론 API 검토 | W16 이후 | 중 | 고급 기능 실서비스화 |
| 15 | 기능 | 라벨 포맷 내보내기 | 마스크를 COCO / YOLO-seg 폴리곤으로 내보내기 (프로젝트 핵심 목적: 학습 데이터 준비) | W16 이후 | 중 | AI 학습 데이터 직접 활용 |
| 16 | 기능 | 브라우저 로컬 추론 | ONNX Runtime Web / WebGPU로 서버 전송 없이 배경 제거 | W16 이후 | 하 | 개인정보 보호·서버 비용 |
| 17 | 기능 | 이미지 합성 편집기 | 추출 객체를 새 배경에 배치·크기 조절·그림자 합성 | W16 이후 | 하 | 편집·합성 활용도 |
| 완료 — 07-27판 계획 중 끝난 항목 |   |   |   |   |   |   |
| 18 | AI | 정확도 검증 · LLM 해석 고도화 | 평가셋·DAVIS·섞임 측정 도구, 키워드 파서·해석 체인·RAG·LoRA (docs/vaildates) | 완료 |   |   |
| 19 | 품질 | 테스트 코드 | 백엔드 463 · 프론트 65 · 콘솔 21 + CI | 완료 |   |   |
| 20 | AI | Grounding DINO + SAM2 | 코드·임계값 측정 완료, 기본 꺼짐(가중치 필요) | 완료 |   |   |
| 21 | AI | Smart Feedback Loop | 피드백 → 학습 DB → 콘솔 검수 → RAG · retrain_lora/yolo | 완료 |   |   |
| 22 | 백엔드 | 배치 500장 · DB 도입 | 배치 API·zip, MariaDB/SQLite 서비스·학습 DB | 완료 |   |   |
| 23 | AI | 영상 지원 | mp4·흔들림 보정·추적·배경판 지우기 + GIF | 완료 |   |   |
| 24 | 인프라 | 배포 구성 · CI/CD | Compose·HTTPS·GPU 오버레이·배포 도구·GitHub Actions (실서버 가동만 남음) | 완료 |   |   |
| 25 | 기능 | 사용자 계정·히스토리 | 회원가입·로그인·찾기·내 계정·작업 기록 (OAuth 대신 아이디/비밀번호) | 완료 |   |   |
| 26 | 보안 | Rate Limit · 인증 | 비로그인/회원 속도 제한, 세션 인증, 업로드 검증 | 완료 |   |   |
| 리스크 및 대응 |   |   |   |   |   |   |
| R1 | 리스크 | ARM CPU 서버 성능 | GPU 없음 → 세그 ONNX·슬림 이미지, LLM 은 e4b 또는 외부 API, 무거운 기능(오픈 보캐브·27b)은 끔 | 배포 | 상 |   |
| R2 | 리스크 | OCI Always Free 용량 부족 | A1 인스턴스 생성 시 '용량 부족'이 나면 다른 가용 도메인·시간대 재시도, OCPU 축소 | 배포 | 중 |   |
| R3 | 리스크 | Worker 경유 긴 요청 끊김 | 영상·GIF·큰 모델 첫 호출은 실제 요청으로 확인, 필요 시 서버 주소 직접 사용 | 배포 | 중 |   |
| R4 | 리스크 | 개인정보·보관 | 처리방침과 실제 보관 기간 일치(24시간·30일), 운영자 정보·동의 기록 | 운영 | 상 |   |
| R5 | 리스크 | 1인 개발 자원·시간 | 배포 우선, 재학습은 데이터가 쌓인 뒤, 문서·검증 기록 유지 | 전체 | 상 |   |
| R6 | 리스크 | 움직이는 카메라·닮은 두 사람 | 영상 지우기 18/30 예전 방식, 닮은 두 사람 추적 93.5% — 한계로 가이드에 안내 | AI | 중 |   |

## 변경_이력

CutNKeep 프로젝트 관련 스프레드 시트 문서

| 변경 이력  \|  2026-07-27판 → 2026-10-11판 시트별 변경 요약 |   |
| --- | --- |
| 시트 | 변경 내용 |
| 공통 | 기준을 07-27 커밋 → develop 4468283 (2026-10-11) 로 갱신 (커밋 395건). 새 항목은 초록 칸으로 표시, 상태 칸 색 구분(구현=초록, 진행/선택=노랑, 예정=회색) |
| 프로젝트_총기획 | 현재 상태(Phase 1~3 코드 완료), 실제 개발 기간, 핵심 기능(지우기·GIF·영상·계정·콘솔), 기술 스택(YOLO26m-seg·SegFormer·LaMa·LangGraph 1.2·FastAPI 0.143·MariaDB), 성공 기준 달성 수치, 보안 정책 갱신. '7. 배포 환경 (Oracle Cloud)' 절 신규 |
| 기능_설계 | 25개 → 53개. 스텁/예정이던 배치·LoRA·Pseudo Labeling·평가·영상·오픈 보캐브를 구현으로 변경, 계정·콘솔·GIF·지우기·추적·배포 도구 등 신규, OCI 실서버 배포는 '진행 중' |
| 용어_정리 | 33개 → 62개. YOLOv8n-seg → YOLO26m-seg, LaMa·SegFormer·배경판·매트·섞임·해석 체인·RAG·Caddy·Cloudflare Worker·OCI·A1.Flex·VCN·보안 목록 등 추가 |
| 테이블_명세서 | PostgreSQL 설계안(6개) → 실제 ORM 7개(users·auth_sessions·auth_codes·jobs·batch_jobs + 학습 DB feedbacks·learning_samples). parsed_prompts·pseudo_labels·model_versions 제거 사유 기록 |
| 스키마_설계 | 관계(CASCADE/SET NULL, DB 간 논리 참조), 인덱스, API 스키마(계정·GIF·Job·콘솔), GraphState 필드·노드 흐름, 파일 저장 경로(런타임/학습 공유 분리) 갱신 |
| URL_설계 | 16개 → 74개. API 46개(계정 11·콘솔 18 포함), 사용자 화면 15개, 콘솔 메뉴 8개, 배포 주소·포트 5개 |
| 화면_설계 | 11개 → 사용자 14 + 콘솔 6. 작업실(사진·GIF)·영상·배치·내 계정·작업 상세·가이드·인증·법적 고지 반영 |
| 간트_차트 | 가정 일정(2026-10-12 시작 10주) → 실제 커밋 일정(2026-07-27 시작 16주). 완료 13건, 배포·운영·마무리 4건, 현재 주 W11 표시 |
| 향후_계획 | OCI 배포 단기 계획(인스턴스·VCN·보안 목록 22/80/443·도메인·점검) 신규, 07-27판 완료 항목 정리, 리스크 갱신(ARM CPU·용량·Worker) |
| ERD | cutnkeep/erd/cutnkeep_erd_2026-10-11.(png·dbml·mmd·html) — 서비스 DB/학습 DB 두 영역으로 다시 그림 |
