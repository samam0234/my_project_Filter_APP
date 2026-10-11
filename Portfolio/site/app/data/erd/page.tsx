import { Shell } from "@/components/Shell";

export default function ErdPage() {
  return (
    <Shell current="/data/erd">
      <header className="page-head">
        <div className="kicker">DATA · 2026-10-11 HTML</div>
        <h1>ERD</h1>
        <p className="lede">
          원본 HTML이 표와 까마귀발 선을 그립니다. 아래 프레임은 그 파일을 그대로 보여 줍니다. 폭은 1780px이라 가로로 스크롤됩니다.
        </p>
      </header>

      <section className="section">
        <iframe className="erd-frame" title="CutNKeep ERD" src="/erd/cutnkeep_erd_2026-10-11.html" />
        <p>
          그림 파일은 <a href="/erd/cutnkeep_erd_2026-10-11.png">PNG</a>로도 있습니다.
          서비스 DB와 학습 DB는 외래 키로 연결되어 있지 않습니다. 실선은 실제 외래 키, 점선은 값 참조입니다.
        </p>
      </section>

      <section className="section">
        <h2>그림에 있는 표</h2>
        <div className="grid two">
          <article className="card">
            <strong>서비스 DB</strong>
            <p>users, auth_sessions, auth_codes, jobs, batch_jobs. 회원 삭제 시 세션과 코드는 함께 지워지고, 작업의 회원 칸은 비웁니다.</p>
          </article>
          <article className="card">
            <strong>학습 DB</strong>
            <p>feedbacks, learning_samples. 피드백 1건에서 문장 샘플과 세그 샘플이 최대 두 건 나옵니다. origin_id와 kind가 유일합니다.</p>
          </article>
        </div>
      </section>

      <section className="section">
        <h2>그림 다음에 생긴 표</h2>
        <div className="note">
          이메일 인증 가입의 signup_pending은 이 HTML에 없습니다. 인증 전 가입 정보를 최대 30분 두고, 인증하면 users로 옮긴 뒤 지웁니다.
          제품 AI 채팅과 이 사이트의 안내 챗은 테이블이 없습니다. 대화를 저장하지 않기 때문입니다.
        </div>
        <div className="table-wrap">
          <table>
            <thead><tr><th>signup_pending</th><th>의미</th></tr></thead>
            <tbody>
              <tr><td>email</td><td>유일</td></tr>
              <tr><td>username, display_name, password_hash</td><td>가입 정보. 비밀번호는 해시</td></tr>
              <tr><td>terms_agreed_at</td><td>만 14세·약관·처리방침 동의 시각</td></tr>
              <tr><td>code_hash, attempts, expires_at</td><td>일련번호 8글자. 5회, 30분</td></tr>
            </tbody>
          </table>
        </div>
      </section>
    </Shell>
  );
}
