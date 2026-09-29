/**
 * 사용자 앱 루트 (Vite :5173) — 경로별 페이지 선택.
 *
 * | 경로          | 페이지            |
 * |---------------|-------------------|
 * | /             | 홈                |
 * | /studio       | 작업실 (배경 제거) |
 * | /history      | 작업 기록         |
 * | /jobs/:id     | 작업 상세         |
 * | /guide        | 프롬프트 가이드   |
 * | /batch        | 배치 (Phase 2)    |
 *
 * 라우터: ./router.tsx (History API). 상태: useAppStore (작업실 입력·결과 유지).
 */
import { useEffect } from "react";
import { AppLayout } from "./components/layout/AppLayout";
import { BatchPage } from "./pages/BatchPage";
import { GuidePage } from "./pages/GuidePage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { StudioPage } from "./pages/StudioPage";
import { matchRoute, usePathname } from "./router";

const TITLES: Record<string, string> = {
  "/": "홈",
  "/studio": "작업실",
  "/history": "작업 기록",
  "/guide": "프롬프트 가이드",
  "/batch": "배치",
};

function Page({ pathname }: { pathname: string }) {
  if (matchRoute("/", pathname)) return <HomePage />;
  if (matchRoute("/studio", pathname)) return <StudioPage />;
  if (matchRoute("/history", pathname)) return <HistoryPage />;
  if (matchRoute("/guide", pathname)) return <GuidePage />;
  if (matchRoute("/batch", pathname)) return <BatchPage />;
  const job = matchRoute("/jobs/:id", pathname);
  if (job) return <JobDetailPage jobId={job.id} />;
  return <NotFoundPage />;
}

export default function App() {
  const pathname = usePathname();

  useEffect(() => {
    const base = pathname.startsWith("/jobs/") ? "작업 상세" : TITLES[pathname] ?? "페이지 없음";
    document.title = `${base} · 컷앤킵`;
  }, [pathname]);

  return (
    <AppLayout>
      <Page pathname={pathname} />
    </AppLayout>
  );
}
