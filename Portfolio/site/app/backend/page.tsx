import { Shell, Shot } from "@/components/Shell";

export default function BackendPage() {
  return (
    <Shell current="/backend">
      <header className="page-head">
        <div className="kicker">BACKEND · FastAPI :8000</div>
        <h1>백엔드 서버</h1>
        <p className="lede">
          문장을 구조로 바꾸고, 마스크를 만들고, 효과를 적용하고, 회원에게만 기록합니다. 이 포트폴리오의 Flask 안내와는 다른 프로그램입니다.
        </p>
      </header>

      <section className="section">
        <h2>개요</h2>
        <p>
          계층은 라우터, 스키마, 서비스·워크플로, 레포지토리, ORM, DB입니다. 라우터는 SQL을 직접 쓰지 않고, 레포지토리는 OpenCV와 LLM을 모릅니다.
          Docker 프로젝트 이름은 <code>cut_and_keep</code>입니다. 서비스는 frontend, backend, mariadb, redis, adminer, mariadb-backup입니다.
          Celery 워커는 프로필 phase2일 때만 있고, 기본 배치는 API 프로세스에서 한 장씩 처리합니다.
        </p>
        <p>
          운영은 Oracle Cloud A1.Flex, ARM 4 OCPU, 메모리 24GB입니다. 공개 포트는 22, 80, 443뿐입니다.
          Caddy가 인증서를 맡고, Cloudflare Worker가 화면과 API 프록시를 맡습니다. 문장 해석은 운영자 PC의 Ollama로 SSH 터널을 탑니다.
        </p>
      </section>

      <section className="section">
        <h2>엔진</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>영역</th><th>선택</th></tr></thead>
            <tbody>
              <tr><td>API</td><td>FastAPI 0.143, Pydantic 2, Uvicorn</td></tr>
              <tr><td>서비스 DB</td><td>Docker MariaDB 11. 호스트 개발은 SQLite</td></tr>
              <tr><td>학습 DB</td><td>MariaDB. 꺼지면 SQLite로 잠시 대체</td></tr>
              <tr><td>큐</td><td>Redis 7. 호스트 6380. Celery는 선택</td></tr>
              <tr><td>이미지</td><td>OpenCV. 경계, 겹침 제거, Telea</td></tr>
              <tr><td>계정</td><td>scrypt, HttpOnly 쿠키, 이메일 일련번호</td></tr>
            </tbody>
          </table>
        </div>
        <div className="note">/health의 phase 상수는 1입니다. 기능이 그 다음 단계까지 있어도 이 숫자는 스모크 테스트 때문에 바꾸지 않습니다.</div>
      </section>

      <section className="section">
        <h2>상세 기능</h2>
        <p>
          LangGraph 노드는 해석, 전처리, 세그, 검증, 효과, 피드백입니다. 검증이 약하면 전처리를 반대로 하고 기준을 낮춰 한 번 더 찾은 뒤 더 나은 마스크를 고릅니다.
          효과는 배경 제거, 블러, 크롭, 대상 지우기입니다. 사진 지우기는 LaMa, 없으면 Telea입니다. 영상과 GIF는 다른 프레임에서 모은 배경판을 씁니다.
          회원 파일은 24시간, 실패 사진은 30일, 로그는 14일, MariaDB 덤프는 매일 7일입니다. 덤프는 같은 디스크입니다.
        </p>
      </section>

      <section className="section">
        <h2>API</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>묶음</th><th>대표</th></tr></thead>
            <tbody>
              <tr><td>상태</td><td>GET /health</td></tr>
              <tr><td>처리</td><td>POST /api/v1/upload, /gif, /video</td></tr>
              <tr><td>기록</td><td>GET /api/v1/jobs. 소유자가 아니면 404</td></tr>
              <tr><td>피드백·배치</td><td>POST /feedback, /batch 최대 500</td></tr>
              <tr><td>계정</td><td>/auth/signup/start, /signup/verify, /login, /me, 탈퇴</td></tr>
              <tr><td>해석·채팅</td><td>GET /llm/models, POST /chat</td></tr>
              <tr><td>콘솔</td><td>/console/* 관리자</td></tr>
            </tbody>
          </table>
        </div>
        <p>업로드는 확장자, MIME, 시그니처, 해상도를 봅니다. 사진은 약 20MB, 영상은 80MB입니다. production에서 위험한 기본값이면 프로세스가 뜨지 않습니다.</p>
      </section>

      <section className="section">
        <h2>내부에서 보는 장면</h2>
        <p>
          백엔드는 사용자용 HTML이 거의 없습니다. 떠 있는 설정은 콘솔 시스템 화면으로 보고, 처리 결과는 사용자 앱으로 봅니다.
          아래 인페인트와 배경 덩어리는 실험 문서의 결과 그림입니다.
        </p>
        <div className="shots">
          <Shot src="/shots/console-system.png" alt="백엔드 설정이 보이는 시스템 화면" caption="시스템 화면. 세그 런타임, 지우기 엔진, 저장 공간을 여기서 확인합니다." />
          <Shot src="/shots/studio-design.jpg" alt="처리 결과가 보이는 작업실" caption="처리 결과. 해석 칩과 원본/결과가 백엔드 파이프라인의 출력입니다." />
          <Shot src="/shots/inpaint.jpg" alt="대상 지우기 전후" caption="대상 지우기 실험. 빈 자리를 주변 무늬로 메웁니다." />
          <Shot src="/shots/stuff.jpg" alt="배경 덩어리 인식" caption="건물·하늘 같은 배경 덩어리. SegFormer ADE20K." />
        </div>
      </section>

      <section className="section">
        <h2>고급 기술</h2>
        <ul className="clean">
          <li>LangGraph 1.2가 재시도와 최선 시도를 관리합니다.</li>
          <li>LangChain 해석 체인이 LLM과 키워드 파서를 비교합니다. 처음 보는 문장 86.7%에서 96.7%로 오른 기록이 있습니다.</li>
          <li>RAG는 승인 문장을 글자 n-gram으로 찾고, 확인된 문장은 Chroma에서 한 건 더합니다. 임베딩 모델은 받지 않습니다.</li>
          <li>ONNX 경로는 torch 없이 YOLO를 돌립니다. 슬림 이미지는 약 1.1GB입니다.</li>
          <li>OpenAI와 Gemini는 설정으로만 연결되어 있고 운영 기본값이 아닙니다. 켜면 문장이 밖으로 나갑니다.</li>
        </ul>
      </section>

      <section className="section">
        <h2>문제와 개선</h2>
        <ul className="clean">
          <li>해석이 PC Ollama에 의존합니다. 터널이 끊기면 키워드 파서입니다.</li>
          <li>ARM 서버에서는 GPU 오버레이와 LoRA를 쓰지 않습니다.</li>
          <li>서버 밖 백업이 없고, 스키마 도구 Alembic도 아직입니다.</li>
          <li>오픈 보캐브 가중치는 없고 플래그는 꺼져 있습니다.</li>
          <li>움직이는 카메라의 영상 지우기는 일부 클립이 예전 방식입니다.</li>
        </ul>
        <div className="future">
          추가하려는 서버: GPU 추론 기계, 서버 밖 백업, 처리방침을 고친 뒤의 문장 전용 외부 해석. 사진은 외부 모델에 보내지 않는 원칙을 유지합니다.
        </div>
      </section>

      <section className="section">
        <h2>이후</h2>
        <p>
          공개면은 80과 443만 둡니다. 데이터베이스, Redis, Adminer는 루프백입니다.
          보관 기간을 바꾸면 처리방침 문구를 같은 커밋에서 고칩니다. 한 번 어긋난 적이 있습니다.
        </p>
      </section>
    </Shell>
  );
}
