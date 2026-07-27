const links = [
  {
    title: "사용자 앱 (Frontend)",
    href: "http://localhost:5173",
    desc: "업로드 · 프롬프트 · Before/After",
  },
  {
    title: "Backend API Docs",
    href: "http://localhost:8000/docs",
    desc: "Swagger UI",
  },
  {
    title: "Health",
    href: "http://localhost:8000/health",
    desc: "JSON 헬스체크",
  },
  {
    title: "문서 허브",
    href: "../docs/README.md",
    desc: "로컬 파일 경로 — IDE에서 docs/README.md 참고",
  },
];

export function LinksPage() {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-semibold text-white">바로가기</h2>
        <p className="mt-1 text-sm text-console-muted">
          운영 중 자주 여는 엔드포인트 · 앱
        </p>
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        {links.map((l) => (
          <a
            key={l.title}
            href={l.href.startsWith("http") ? l.href : undefined}
            target={l.href.startsWith("http") ? "_blank" : undefined}
            rel="noreferrer"
            className="block rounded-xl border border-console-border bg-console-panel p-4 transition hover:border-console-accent/50"
          >
            <p className="font-medium text-console-accent">{l.title}</p>
            <p className="mt-1 text-sm text-slate-300">{l.desc}</p>
            <p className="mt-2 font-mono text-xs text-console-muted">{l.href}</p>
          </a>
        ))}
      </div>
    </div>
  );
}
