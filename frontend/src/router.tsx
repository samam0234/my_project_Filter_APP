/**
 * 최소 URL 라우터 (History API).
 *
 * react-router 없이 페이지 6개를 나누기 위한 얇은 구현:
 *  - usePathname : 현재 경로 구독 (popstate + navigate 알림)
 *  - navigate    : pushState 후 구독자 알림 + 스크롤 맨 위
 *  - matchRoute  : "/jobs/:id" 같은 패턴 매칭 → params
 *  - Link        : 새 탭(⌘/Ctrl/휠 클릭)은 브라우저 기본 동작 유지
 *
 * 새로고침·직접 접근은 Vite dev 서버와 nginx(try_files → index.html)가 index.html 로 돌려준다.
 */
import {
  useSyncExternalStore,
  type AnchorHTMLAttributes,
  type MouseEvent,
  type ReactNode,
} from "react";

const listeners = new Set<() => void>();

function subscribe(callback: () => void): () => void {
  listeners.add(callback);
  window.addEventListener("popstate", callback);
  return () => {
    listeners.delete(callback);
    window.removeEventListener("popstate", callback);
  };
}

/** 현재 pathname (예: "/jobs/abc"). 변경 시 리렌더. */
export function usePathname(): string {
  return useSyncExternalStore(subscribe, () => window.location.pathname);
}

/** 현재 쿼리 문자열 (예: "?status=ok"). */
export function useSearch(): string {
  return useSyncExternalStore(subscribe, () => window.location.search);
}

/** 앱 안 이동. replace=true 면 히스토리를 남기지 않음 (필터 변경 등). */
export function navigate(to: string, { replace = false } = {}): void {
  const current = window.location.pathname + window.location.search;
  if (to === current) return;
  if (replace) window.history.replaceState(null, "", to);
  else window.history.pushState(null, "", to);
  listeners.forEach((notify) => notify());
  if (!replace) window.scrollTo({ top: 0 });
}

/** "/jobs/:id" 와 "/jobs/abc" → { id: "abc" }. 불일치면 null. */
export function matchRoute(pattern: string, pathname: string): Record<string, string> | null {
  const trim = (s: string) => s.replace(/\/+$/, "") || "/";
  const a = trim(pattern).split("/");
  const b = trim(pathname).split("/");
  if (a.length !== b.length) return null;
  const params: Record<string, string> = {};
  for (let i = 0; i < a.length; i += 1) {
    if (a[i].startsWith(":")) params[a[i].slice(1)] = decodeURIComponent(b[i]);
    else if (a[i] !== b[i]) return null;
  }
  return params;
}

interface LinkProps extends Omit<AnchorHTMLAttributes<HTMLAnchorElement>, "href"> {
  to: string;
  children: ReactNode;
}

export function Link({ to, onClick, children, ...rest }: LinkProps) {
  const handle = (e: MouseEvent<HTMLAnchorElement>) => {
    onClick?.(e);
    if (
      e.defaultPrevented ||
      e.button !== 0 ||
      e.metaKey ||
      e.ctrlKey ||
      e.shiftKey ||
      e.altKey ||
      rest.target === "_blank"
    ) {
      return;
    }
    e.preventDefault();
    navigate(to);
  };
  return (
    <a href={to} onClick={handle} {...rest}>
      {children}
    </a>
  );
}
