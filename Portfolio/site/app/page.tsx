import Link from "next/link";
import { GuideStatus } from "@/components/GuideStatus";
import { Shell } from "@/components/Shell";

const toc = [
  ["/frontend", "프론트엔드", "사용자 앱. 작업실, 계정, 영상, 배치, 디자인."],
  ["/console", "어드민 콘솔", "검수, 회원, 시스템. 공개 서버에는 올리지 않음."],
  ["/backend", "백엔드 서버", "FastAPI, 저장, 보안, 실서버 배포."],
  ["/ai", "AI 서비스", "YOLO, Ollama, LangChain, RAG, LangGraph, 학습."],
  ["/data/erd", "ERD", "서비스 DB와 학습 DB. 2026-10-11 HTML."],
  ["/data/spreadsheet", "스프레드시트", "기능, URL, 화면, 일정, 이후 계획 10개 시트."],
  ["/project", "프로젝트 소개", "왜 만들었는지와 지금 운영 상태."],
  ["/chat", "안내 챗", "문서를 근거로 설명. 기록은 브라우저만."],
];

export default function HomePage() {
  return (
    <Shell current="/">
      <section className="hero">
        <div>
          <div className="kicker">PORTFOLIO · 2026-10-12</div>
          <h1>한 문장으로 남기거나 지우는 서비스, 컷앤킵</h1>
          <p className="lede">
            컷앤킵은 사진, 움직이는 GIF, 짧은 영상을 올리고 문장으로 대상을 고릅니다.
            이 사이트는 그 제품을 역할별로 설명합니다. 여기서 이미지를 처리하지는 않습니다.
          </p>
          <div className="actions">
            <Link className="btn" href="/frontend">사용자 앱 보기</Link>
            <Link className="btn alt" href="/backend">서버 보기</Link>
            <Link className="btn copper" href="/chat">안내 챗</Link>
          </div>
        </div>
        <aside className="hero-panel">
          <div className="kicker" style={{ color: "#fdba74" }}>읽는 순서</div>
          <ol>
            <li>이 페이지에서 범위만 잡습니다.</li>
            <li>화면, 콘솔, 서버, AI 중 필요한 장으로 갑니다.</li>
            <li>표가 필요하면 ERD와 시트를 엽니다.</li>
            <li>더 묻고 싶으면 안내 챗에 적습니다.</li>
          </ol>
          <GuideStatus />
        </aside>
      </section>

      <section className="section">
        <h2>목차</h2>
        <div className="grid">
          {toc.map(([href, title, text]) => (
            <Link key={href} className="card" href={href}>
              <strong>{title}</strong>
              <p>{text}</p>
              <em>들어가기</em>
            </Link>
          ))}
        </div>
      </section>

      <section className="section">
        <h2>프로젝트</h2>
        <p>
          예시 문장은 “강아지만 남기고 배경 제거”, “맨 앞 빨간 안전모 쓴 사람만”, “오른쪽 사람 지워줘”입니다.
          2026-07-27에 시작했고, 2026-10-11에 Oracle Cloud 공개 배포를 마쳤습니다.
          주소는 <code>https://168-110-17-193.sslip.io</code> 이고, 화면은 Cloudflare Worker <code>cutnkeep-front</code>가 제공합니다.
        </p>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>구성</th><th>기술</th><th>주소</th></tr>
            </thead>
            <tbody>
              <tr><td>사용자 앱</td><td>React, TypeScript, Vite 7</td><td>로컬 5173 · 서버 80 · Worker</td></tr>
              <tr><td>운영 콘솔</td><td>React, TypeScript, Vite 7</td><td>로컬 5174. 서버에는 없음</td></tr>
              <tr><td>백엔드</td><td>FastAPI, MariaDB, Redis</td><td>8000, 공개는 443 뒤</td></tr>
              <tr><td>문장 해석</td><td>Ollama gemma4:e4b 기본</td><td>운영자 PC, SSH 터널</td></tr>
              <tr><td>대상 찾기</td><td>YOLO26m-seg, SegFormer</td><td>오픈 보캐브는 기본 꺼짐</td></tr>
            </tbody>
          </table>
        </div>
      </section>

      <section className="section">
        <h2>기능 요약</h2>
        <div className="grid two">
          <article className="card">
            <strong>누구나</strong>
            <p>배경 제거, 블러, 크롭, 대상 지우기. 처리 후 바로 내려받기. 서버에 파일을 남기지 않습니다.</p>
          </article>
          <article className="card">
            <strong>회원</strong>
            <p>작업 기록, 평가, 정답 알려주기, 최대 500장 배치. 파일은 24시간입니다.</p>
          </article>
          <article className="card">
            <strong>관리자</strong>
            <p>학습 후보 승인, 회원 잠금과 삭제, 디스크 정리. 승인된 문장만 다음 해석의 예시가 됩니다.</p>
          </article>
          <article className="card">
            <strong>확인된 한계</strong>
            <p>해석은 PC의 Ollama가 켜져 있어야 합니다. Worker는 약 100초에서 긴 작업을 끊을 수 있습니다. 서버 밖 백업은 없습니다.</p>
          </article>
        </div>
        <div className="actions">
          <Link className="btn" href="/frontend">프론트엔드</Link>
          <Link className="btn alt" href="/console">어드민 콘솔</Link>
          <Link className="btn alt" href="/ai">AI 서비스</Link>
          <Link className="btn alt" href="/project">프로젝트 소개</Link>
        </div>
      </section>
    </Shell>
  );
}
