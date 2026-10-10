/**
 * 컷앤킵 Cloudflare Worker — /api/* · /health 를 백엔드 서버로 그대로 넘긴다.
 *
 * 화면(정적 파일)과 API 가 같은 주소로 보이므로 로그인 쿠키가 그대로 동작한다.
 * 서버(Caddy)는 속도 제한에 쓰는 접속 IP 를 Cloudflare 가 아닌 실제 사용자 IP 로 알아야 한다:
 *   X-Cnk-Real-IP 에 사용자 IP 를, X-Cnk-Edge 에 비밀 값(EDGE_SECRET)을 실어 보내면
 *   Caddy 가 비밀 값이 맞을 때만 그 IP 를 믿는다 (docker/caddy/Caddyfile).
 */
export default {
  async fetch(request, env) {
    if (!env.EDGE_SECRET) return new Response("EDGE_SECRET 이 설정되지 않았습니다.", { status: 500 });
    const url = new URL(request.url);
    const target = new URL(url.pathname + url.search, env.ORIGIN);

    const headers = new Headers(request.headers);
    // 사용자가 직접 넣은 같은 이름의 헤더는 지우고 Worker 가 확정한 값만 보낸다
    headers.set("X-Cnk-Edge", env.EDGE_SECRET);
    headers.set("X-Cnk-Real-IP", request.headers.get("CF-Connecting-IP") || "");
    headers.delete("X-Real-IP");

    return fetch(target, {
      method: request.method,
      headers,
      body: ["GET", "HEAD"].includes(request.method) ? undefined : request.body,
      redirect: "manual",
    });
  },
};
