import { Shell, Shot } from "@/components/Shell";

export default function FrontendPage() {
  return (
    <Shell current="/frontend">
      <header className="page-head">
        <div className="kicker">FRONTEND · frontend/</div>
        <h1>사용자 앱</h1>
        <p className="lede">
          사진을 올리고 문장을 쓰고 결과를 받는 화면입니다. 데이터베이스에는 직접 붙지 않고 FastAPI만 호출합니다.
        </p>
      </header>

      <section className="section">
        <h2>개요</h2>
        <p>
          React 18, TypeScript, Vite 7, Tailwind, Zustand입니다. 라우터는 <code>src/router.tsx</code>의 History API입니다.
          로컬은 5173, Docker nginx는 80, 공개 화면의 다른 경로는 Cloudflare Worker입니다.
          비로그인은 처리하고 내려받기만 합니다. 기록, 평가, 배치, 내 계정은 회원만 씁니다.
        </p>
      </section>

      <section className="section">
        <h2>엔진</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>역할</th><th>선택</th></tr></thead>
            <tbody>
              <tr><td>화면</td><td>React 함수 컴포넌트</td></tr>
              <tr><td>상태</td><td>Zustand. 작업, 로그인, 고른 해석 모델</td></tr>
              <tr><td>글꼴</td><td>Pretendard. 빌드에 포함하고 CDN은 쓰지 않음</td></tr>
              <tr><td>서버 상태</td><td>머리글 점. 30초마다 GET /health</td></tr>
              <tr><td>테스트</td><td>Vitest 5. 인수인계 기준 95개 통과</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>상세 기능</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>경로</th><th>하는 일</th></tr></thead>
            <tbody>
              <tr><td>/</td><td>비교 데모, 예시 문장, 사용 순서, 최근 작업</td></tr>
              <tr><td>/studio</td><td>사진. 올리기, 문장, 처리. 해석 칩과 원본/결과</td></tr>
              <tr><td>/studio?type=gif</td><td>GIF. 간격·반복 유지, 최대 120프레임, 투명 GIF와 WebP</td></tr>
              <tr><td>/video</td><td>최대 20초·80MB. mp4. 마지막 결과는 브라우저 IndexedDB</td></tr>
              <tr><td>/batch</td><td>회원. 같은 문장으로 최대 500장, 진행률, zip</td></tr>
              <tr><td>/account</td><td>내 정보, 기록, 보안, 탈퇴</td></tr>
              <tr><td>/jobs/:id</td><td>다시 보기, 해석 JSON, 같은 문장으로 재작업</td></tr>
              <tr><td>/guide</td><td>문장 쓰는 법. 탭으로 AI 채팅</td></tr>
              <tr><td>/signup/verify</td><td>메일 일련번호 8글자. 30분, 5회</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          해석 모델 상자는 e4b, 12b, 27b를 고릅니다. 서버에 없으면 “미적용”입니다.
          GPU 서버가 LoRA로 해석하면 상자는 숨고, 배치는 서버 기본 모델만 씁니다.
        </p>
      </section>

      <section className="section">
        <h2>API 연결</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>동작</th><th>호출</th></tr></thead>
            <tbody>
              <tr><td>사진</td><td>POST /api/v1/upload</td></tr>
              <tr><td>GIF</td><td>POST /api/v1/gif</td></tr>
              <tr><td>영상</td><td>POST /api/v1/video, GET /api/v1/video/{"{id}"}</td></tr>
              <tr><td>기록·파일</td><td>GET /api/v1/jobs, GET /api/v1/files/{"{id}"}/*</td></tr>
              <tr><td>평가</td><td>POST /api/v1/feedback</td></tr>
              <tr><td>배치</td><td>POST/GET /api/v1/batch, 항목, zip</td></tr>
              <tr><td>계정</td><td>/api/v1/auth/* HttpOnly 쿠키</td></tr>
              <tr><td>모델·채팅</td><td>GET /api/v1/llm/models, POST /api/v1/chat</td></tr>
            </tbody>
          </table>
        </div>
        <div className="note">
          제품의 AI 채팅은 요청 문장을 만들어 작업실에 넣는 기능입니다. 이 사이트의 안내 챗과는 다른 프로세스입니다.
          제품 채팅도 서버에 대화를 저장하지 않습니다.
        </div>
      </section>

      <section className="section">
        <h2>내부 화면</h2>
        <div className="shots">
          <Shot src="/shots/home-design.jpg" alt="홈 화면 디자인 전후" caption="2026-10-08 홈. 위는 이전, 아래는 비교 슬라이더가 있는 이후." />
          <Shot src="/shots/home-run.png" alt="실행 중인 홈" caption="실행 중인 홈. 예시 문장과 사용 순서가 보입니다." />
          <Shot src="/shots/studio-design.jpg" alt="작업실 디자인 전후" caption="작업실. 1 사진, 2 문장, 3 처리와 실제 결과." />
          <Shot src="/shots/mobile-menu.jpg" alt="모바일 펼침 메뉴" caption="1024px 미만. 메뉴 이름이 보이는 펼침 메뉴." />
          <Shot src="/shots/mobile-studio.png" alt="좁은 작업실" caption="좁은 화면의 작업실." />
          <Shot src="/shots/history.png" alt="작업 기록" caption="회원 작업 기록. 종류와 상태 필터." />
          <Shot src="/shots/job-detail.png" alt="작업 상세" caption="작업 상세. 결과와 해석을 다시 봅니다." />
          <Shot src="/shots/video.png" alt="영상 처리 화면" caption="회원 영상 처리. 결과는 mp4로 재생합니다." />
          <Shot src="/shots/batch.png" alt="배치 완료 화면" caption="배치 완료. 항목 결과와 실패 표시." />
        </div>
      </section>

      <section className="section">
        <h2>디자인</h2>
        <p>
          다크 테마를 유지했습니다. 한국어는 낱말 중간에서 끊기지 않게 <code>keep-all</code>을 씁니다.
          키보드 초점 링과 움직임 줄이기를 따릅니다. 홈 데모 그림은 초상권 때문에 실제 사진이 아니라 SVG입니다.
          2026-10-08 확인에서 1440과 390 너비의 가로 스크롤은 없었습니다.
        </p>
      </section>

      <section className="section">
        <h2>문제와 개선</h2>
        <ul className="clean">
          <li>반영함: 줄바꿈, 모바일 메뉴, 작업실 단계, 이메일 인증 가입, 영상·배치 화면.</li>
          <li>아직: Worker 약 100초 제한. 27b, 모델 교체 직후의 12b, 긴 영상·GIF는 서버 주소가 여유가 있습니다.</li>
          <li>아직: 실제 휴대폰, 실제 메일함의 가입 버튼, 접근성 자동 점검은 인수인계에 미검증으로 남아 있습니다.</li>
          <li>아직: 채팅 스트리밍, 이메일 변경, 기존 회원 재인증은 없습니다.</li>
        </ul>
        <div className="future">
          예정: 마스크를 COCO·YOLO 형식으로 내려받기, 브라우저 로컬 ONNX, 채팅을 나누어 받기.
        </div>
      </section>

      <section className="section">
        <h2>이후</h2>
        <p>
          화면 흐름은 올리기, 문장, 결과, 회원만 기록으로 유지합니다.
          자체 도메인이 생기면 Worker의 원본 주소와 운영자 표기를 같이 바꿉니다.
          로컬에서 콘솔과 사용자 앱은 쿠키를 공유합니다. 포트가 달라도 같은 계정이 됩니다.
        </p>
      </section>
    </Shell>
  );
}
