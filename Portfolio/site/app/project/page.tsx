import Link from "next/link";
import { Shell } from "@/components/Shell";

export default function ProjectPage() {
  return (
    <Shell current="/project">
      <header className="page-head">
        <div className="kicker">PROJECT</div>
        <h1>프로젝트 소개</h1>
        <p className="lede">
          컷앤킵은 이미지에서 대상을 가려 내는 일을 펜 대신 한 문장으로 줄이려는 서비스입니다.
          수익 모델과 사업자 등록은 저장소에 없어 이 페이지도 지어내지 않습니다.
        </p>
      </header>

      <section className="section">
        <h2>무슨 일인가</h2>
        <p>
          학습 데이터를 만들 때 수천 장에 사각형을 두르는 작업은 느리고, 사각형은 물체의 가장자리를 담지 못합니다.
          “이것만 남기고”, “저것만 지우고”를 말하면 픽셀 마스크로 그 영역만 다루게 하는 것이 이 일의 범위입니다.
        </p>
        <p>
          1인 개발입니다. 대학생이자 BiNCS AI·데이터 엔지니어 훈련 과정의 작업이고, 구현에는 코딩 도우미를 함께 썼습니다.
          저장소는 github.com/samam0234/my_project_Filter_APP 입니다. 통합은 develop, 공개 서버는 main입니다.
          작업은 feature 브랜치에서만 합니다.
        </p>
      </section>

      <section className="section">
        <h2>누구를 위한가</h2>
        <div className="table-wrap">
          <table>
            <thead><tr><th>사용자</th><th>얻는 것</th></tr></thead>
            <tbody>
              <tr><td>급히 갈라 내야 하는 사람</td><td>가입 없이 처리하고 내려받기</td></tr>
              <tr><td>다시 봐야 하는 회원</td><td>24시간 기록, 평가, 배치</td></tr>
              <tr><td>모델을 고치는 운영자</td><td>콘솔 검수, 재학습 스크립트, 실험 기록</td></tr>
              <tr><td>다음 담당자</td><td>인수인계 문서 한 장</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>업무로 보면</h2>
        <p>
          범위는 사용자 앱, 운영 콘솔, API 서버, 학습 도구 네 가지입니다.
          배포는 Oracle Cloud ARM, Caddy 인증서, Cloudflare 화면, 운영자 PC의 Ollama입니다.
          메일은 가입 인증, 아이디 찾기, 비밀번호 재설정만 보냅니다.
        </p>
        <ul className="clean">
          <li>비밀 값은 저장소에 두지 않습니다.</li>
          <li>비로그인 파일은 저장하지 않습니다. 회원 파일은 24시간, 실패 분석 사진은 30일입니다.</li>
          <li>공개 포트는 웹과 SSH뿐입니다. 콘솔은 아직 공개 주소에 없습니다.</li>
          <li>되지 않은 일은 되었다고 적지 않습니다.</li>
        </ul>
      </section>

      <section className="section">
        <h2>지금 상태</h2>
        <p>
          서비스는 공개 URL로 열려 있습니다. 자체 도메인과 운영자 실명은 빠져 있습니다.
          비용은 Always Free 구간의 ARM 서버와, 해석을 떠안는 운영자 PC입니다.
          서버만으로 큰 언어 모델을 돌리지 못하는 것이 가장 큰 제약입니다.
        </p>
        <div className="grid two">
          <article className="card">
            <strong>맡은 일</strong>
            <p>한국어 문장을 편집 명령으로 바꾸기, 마스크, 사진·GIF·짧은 영상, 계정과 보관 기간, 검수 뒤에만 학습.</p>
          </article>
          <article className="card">
            <strong>맡지 않은 일</strong>
            <p>실시간 방송, 얼굴 식별, 가중치 없는 오픈 보캐브의 운영, 콘솔 공개, 서버 밖 백업.</p>
          </article>
        </div>
      </section>

      <section className="section">
        <h2>다음 업무</h2>
        <ol className="clean">
          <li>PC가 꺼져도 해석이 되는 경로.</li>
          <li>서버 밖 백업.</li>
          <li>자체 도메인과 운영자 표기.</li>
          <li>실패 사진과 승인 문장이 쌓이면 재학습.</li>
          <li>마스크를 학습 형식 파일로 내보내기.</li>
        </ol>
        <p>
          2026-10-11 시트가 “배포 진행 중”으로 둔 항목은 다음 날 인수인계에서 공개 운영으로 닫혔습니다.
        </p>
        <div className="actions">
          <Link className="btn" href="/frontend">화면으로</Link>
          <Link className="btn alt" href="/terms">이용약관</Link>
          <Link className="btn alt" href="/data/spreadsheet">향후 계획 시트</Link>
        </div>
      </section>
    </Shell>
  );
}
