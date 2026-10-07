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
 * | /batch        | 배치 (회원 전용)  |
 * | /video        | 영상              |
 * | /login        | 로그인            |
 * | /signup       | 회원가입          |
 * | /find-id      | 아이디 찾기       |
 * | /find-password| 비밀번호 찾기     |
 *
 * 앱 시작 시 /auth/me 로 로그인 상태를 확인한다 (세션은 HttpOnly 쿠키).
 * 이미 로그인한 사용자가 로그인·가입 화면에 오면 next(또는 홈)로 보낸다.
 * 라우터: ./router.tsx (History API). 상태: useAppStore (작업실 입력·결과 유지).
 */
import { useEffect } from "react";
import { safeNext } from "./components/auth/AuthForm";
import { AppLayout } from "./components/layout/AppLayout";
import { BatchPage } from "./pages/BatchPage";
import { GuidePage } from "./pages/GuidePage";
import { HistoryPage } from "./pages/HistoryPage";
import { HomePage } from "./pages/HomePage";
import { JobDetailPage } from "./pages/JobDetailPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { StudioPage } from "./pages/StudioPage";
import { VideoPage } from "./pages/VideoPage";
import { FindIdPage } from "./pages/auth/FindIdPage";
import { FindPasswordPage } from "./pages/auth/FindPasswordPage";
import { LoginPage } from "./pages/auth/LoginPage";
import { SignupPage } from "./pages/auth/SignupPage";
import { matchRoute, navigate, usePathname, useSearch } from "./router";
import { useAuthStore } from "./store/useAuthStore";

const TITLES: Record<string, string> = {
  "/": "홈",
  "/studio": "작업실",
  "/history": "작업 기록",
  "/guide": "프롬프트 가이드",
  "/batch": "배치",
  "/video": "영상",
  "/login": "로그인",
  "/signup": "회원가입",
  "/find-id": "아이디 찾기",
  "/find-password": "비밀번호 찾기",
};

/** 로그인 상태면 들어올 필요 없는 화면 */
const GUEST_ONLY = new Set(["/login", "/signup", "/find-id", "/find-password"]);

function Page({ pathname }: { pathname: string }) {
  if (matchRoute("/", pathname)) return <HomePage />;
  if (matchRoute("/studio", pathname)) return <StudioPage />;
  if (matchRoute("/history", pathname)) return <HistoryPage />;
  if (matchRoute("/guide", pathname)) return <GuidePage />;
  if (matchRoute("/batch", pathname)) return <BatchPage />;
  if (matchRoute("/video", pathname)) return <VideoPage />;
  if (matchRoute("/login", pathname)) return <LoginPage />;
  if (matchRoute("/signup", pathname)) return <SignupPage />;
  if (matchRoute("/find-id", pathname)) return <FindIdPage />;
  if (matchRoute("/find-password", pathname)) return <FindPasswordPage />;
  const job = matchRoute("/jobs/:id", pathname);
  if (job) return <JobDetailPage jobId={job.id} />;
  return <NotFoundPage />;
}

export default function App() {
  const pathname = usePathname();
  const search = useSearch();
  const authStatus = useAuthStore((s) => s.status);
  const refreshAuth = useAuthStore((s) => s.refresh);

  useEffect(() => {
    void refreshAuth();
  }, [refreshAuth]);

  useEffect(() => {
    if (authStatus === "user" && GUEST_ONLY.has(pathname)) {
      navigate(safeNext(search), { replace: true });
    }
  }, [authStatus, pathname, search]);

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
