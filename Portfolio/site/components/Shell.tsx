import Link from "next/link";
import { ReadingBar } from "./ReadingBar";

const links = [
  ["/","소개"],
  ["/frontend","프론트엔드"],
  ["/console","어드민"],
  ["/backend","백엔드"],
  ["/ai","AI"],
  ["/data/erd","ERD"],
  ["/data/spreadsheet","시트"],
  ["/chat","안내 챗"],
] as const;

export function Shell({
  current,
  children,
}: {
  current: string;
  children: React.ReactNode;
}) {
  return (
    <>
      <header className="topbar">
        <ReadingBar />
        <div className="topbar-inner">
          <Link className="brand" href="/">
            <i className="mark" aria-hidden="true">컷</i>
            <span className="brand-text">
              <b>컷앤킵 포트폴리오</b>
              <small>설명 사이트 · 제품과 별도</small>
            </span>
          </Link>
          <nav className="nav" aria-label="목차">
            {links.map(([href, label]) => (
              <Link key={href} href={href} aria-current={current === href ? "page" : undefined}>
                {label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main id="content" className="wrap page-in">{children}</main>
      <footer className="footer">
        <div className="footer-inner">
          <div className="footer-links">
            <Link href="/project">프로젝트 소개</Link>
            <Link href="/terms">이용약관</Link>
          </div>
          <p>이 사이트는 컷앤킵을 설명합니다. 사진 처리는 제품 서버에서 하고, 안내 챗 기록은 이 브라우저에만 남습니다.</p>
        </div>
      </footer>
    </>
  );
}

export function Shot({
  src,
  alt,
  caption,
}: {
  src: string;
  alt: string;
  caption: string;
}) {
  return (
    <figure>
      <img src={src} alt={alt} />
      <figcaption>{caption}</figcaption>
    </figure>
  );
}
