import { Shell, Shot } from "@/components/Shell";

export default function ConsolePage() {
  return (
    <Shell current="/console">
      <header className="page-head">
        <div className="kicker">ADMIN · console/</div>
        <h1>운영 콘솔</h1>
        <p className="lede">
          사용자 앱과 같은 React 계열이지만 포트, 배포, 권한이 다릅니다. 서비스를 쓰는 화면이 아니라 서비스를 보는 화면입니다.
        </p>
      </header>

      <section className="section">
        <h2>개요</h2>
        <p>
          로컬 주소는 5174입니다. Docker Compose에 콘솔 서비스는 없고, 공개 서버에도 올리지 않았습니다.
          관리자 PC에서 띄운 뒤 서버의 <code>/api/v1/console/*</code>를 호출합니다.
          <code>CONSOLE_ADMINS</code>에 있는 아이디만 통과합니다. 서버 PC이고 로그인 강제가 꺼져 있으면 예외입니다.
          관리자가 아닌 회원은 세션이 바로 끊깁니다.
        </p>
      </section>

      <section className="section">
        <h2>엔진</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>항목</th><th>내용</th></tr></thead>
            <tbody>
              <tr><td>기술</td><td>TypeScript, Vite 7, Tailwind, Zustand</td></tr>
              <tr><td>갱신</td><td>30초와 수동 새로고침</td></tr>
              <tr><td>테스트</td><td>Vitest 21. 학습 화면이 중심</td></tr>
              <tr><td>검수자 기록</td><td>admin:아이디. 서버 PC는 console:local</td></tr>
              <tr><td>탈퇴</td><td>관리자 계정은 사용자 앱에서 스스로 탈퇴할 수 없음</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>상세 기능</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>메뉴</th><th>내용</th></tr></thead>
            <tbody>
              <tr><td>대시보드</td><td>상태, 집계, 최근 작업</td></tr>
              <tr><td>작업 목록</td><td>전체 회원의 사진·영상·GIF</td></tr>
              <tr><td>배치 현황</td><td>진행과 실패 수. 회원 사진은 보여 주지 않음</td></tr>
              <tr><td>학습 데이터</td><td>승인, 정답 수정 후 승인, 거절, 일괄, 삭제</td></tr>
              <tr><td>회원 관리</td><td>검색, 잠금 해제, 세션 끊기, 삭제</td></tr>
              <tr><td>시스템</td><td>설정 점검, 런타임, 용량, 보관 기간 정리</td></tr>
            </tbody>
          </table>
        </div>
        <p>
          승인된 문장만 RAG와 LoRA에 들어갑니다. 틀린 정답이 다른 사람의 비슷한 요청까지 망가뜨리지 않게 하는 관문입니다.
          승인 시 train/val은 id 해시로 고정되고 val은 약 10%입니다. 삭제는 사이드카 파일까지 지우고 행은 deleted로 남겨 되살아나지 않게 합니다.
        </p>
      </section>

      <section className="section">
        <h2>API 연결</h2>
        <p>
          사용자 앱의 <code>GET /api/v1/jobs</code>는 본인 작업만 돌려주므로 콘솔은 쓰지 않습니다.
          콘솔은 <code>/console/me</code>, <code>/console/jobs</code>, <code>/console/batches</code>, <code>/console/learning/*</code>, <code>/console/users*</code>, <code>/console/system</code>을 씁니다.
          정리는 <code>POST /api/v1/console/system/cleanup</code>입니다. 작업 기록 행은 남고 파일만 지웁니다.
        </p>
      </section>

      <section className="section">
        <h2>내부 화면</h2>
        <p>2026-10-08 디자인 정리는 사용자 앱만 했습니다. 콘솔은 운영용 다크 화면을 유지합니다. 회원 개인정보가 보이는 화면은 여기 넣지 않았습니다.</p>
        <div className="shots">
          <Shot src="/shots/console-login.png" alt="콘솔 로그인" caption="관리자 로그인. 원격에서는 이 화면이 먼저입니다." />
          <Shot src="/shots/console-learning.png" alt="학습 데이터 검수" caption="학습 데이터. 승인 전에 RAG로 들어가지 않습니다." />
          <Shot src="/shots/console-batches.png" alt="배치 현황" caption="전체 배치 현황. 이미지는 보여 주지 않습니다." />
          <Shot src="/shots/console-system.png" alt="시스템 점검" caption="시스템. 설정, 런타임, 저장 공간, 정리." />
        </div>
      </section>

      <section className="section">
        <h2>디자인</h2>
        <p>
          사용자 앱과 같은 빌드 도구를 쓰되, 카드와 타이포 정리는 범위 밖으로 두었습니다.
          표를 빨리 읽고 승인·거절하는 일이 우선입니다. 시스템 화면은 모델을 미리 올리지 않아, 첫 요청 전이면 세그 런타임이 “로드 전”입니다.
        </p>
      </section>

      <section className="section">
        <h2>문제와 개선</h2>
        <ul className="clean">
          <li>반영함: 관리자 로그인, 검수 관문, 회원 잠금·삭제, 실패 사진 30일 정리.</li>
          <li>아직: 공개 주소에 없음. 올리려면 접근 제한이 먼저입니다.</li>
          <li>아직: 리버스 프록시 뒤에서 모든 요청이 127.0.0.1로 보이면 로그인 강제가 느슨할 때 열릴 수 있습니다. 운영 preflight가 경고합니다.</li>
          <li>쓰지 않음: CONSOLE_ALLOW_REMOTE=true. 로그인 없이 여는 예전 방법입니다.</li>
        </ul>
        <div className="future">
          예정: 공개가 필요해지면 접근 제한 후 배포. 재학습 실행은 아직 화면 버튼이 아니라 scripts/retrain_lora.py 입니다. 화면의 재학습 N/200은 그 기준 숫자입니다.
        </div>
      </section>

      <section className="section">
        <h2>이후</h2>
        <p>
          콘솔은 관리자가 적은 도구로 둡니다. 누구나 여는 서비스로 만들지 않습니다.
          학습 품질은 모델 크기보다 이 화면에서 거른 문장에 더 좌우됩니다.
        </p>
      </section>
    </Shell>
  );
}
