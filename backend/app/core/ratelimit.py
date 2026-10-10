"""요청 속도 제한 — 무거운 엔드포인트(업로드: LLM + GPU)를 한 곳에서 과하게 부르지 못하게.

비로그인도 업로드(배경 제거)를 쓸 수 있어 공개 배포 시 남용에 그대로 노출된다.
프로세스 메모리 슬라이딩 윈도우 (워커 1개 기준 · 재시작하면 초기화). 여러 워커·서버로 늘리면 Redis 로 옮길 것.

키: 로그인 회원은 user id, 비로그인은 클라이언트 IP (client_ip).
nginx(Docker frontend) 뒤에서는 모든 요청이 nginx 컨테이너 IP 로 들어와 비로그인 전원이 한 한도를 나눠 썼다 —
TRUSTED_PROXIES 대역에서 온 요청만 nginx 가 덮어쓴 X-Real-IP 를 실제 IP 로 쓴다 (밖에서 보낸 X-Real-IP 는 nginx 가 덮어씀).
콘솔의 "이 PC" 판정(core/access)은 이 값을 쓰지 않는다 — 헤더로 로컬인 척할 수 없게.
"""

from __future__ import annotations

import ipaddress
import threading
import time
from collections import defaultdict, deque
from functools import lru_cache

from fastapi import HTTPException, Request, status


@lru_cache(maxsize=8)
def _networks(spec: str) -> tuple:
    nets = []
    for part in spec.split(","):
        part = part.strip()
        if part:
            try:
                nets.append(ipaddress.ip_network(part, strict=False))
            except ValueError:
                continue
    return tuple(nets)


def client_ip(request: Request, trusted: str | None = None) -> str:
    """속도 제한 키로 쓸 클라이언트 IP. 믿는 프록시(TRUSTED_PROXIES)에서 온 요청이면 X-Real-IP."""
    host = request.client.host if request.client else "unknown"
    if trusted is None:
        from app.core.config import get_settings

        trusted = get_settings().trusted_proxies
    real = (request.headers.get("x-real-ip") or "").strip()
    if not real or not trusted:
        return host
    try:
        addr = ipaddress.ip_address(host)
        ipaddress.ip_address(real)
    except ValueError:
        return host
    return real if any(addr in net for net in _networks(trusted)) else host


class SlidingWindowLimiter:
    def __init__(self, window_seconds: float = 60.0) -> None:
        self.window = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, limit: int, now: float | None = None) -> float:
        """허용되면 0, 막히면 다시 시도까지 남은 초. limit <= 0 이면 제한 없음."""
        if limit <= 0:
            return 0.0
        now = time.monotonic() if now is None else now
        with self._lock:
            q = self._hits[key]
            while q and now - q[0] >= self.window:
                q.popleft()
            if len(q) >= limit:
                return max(0.1, self.window - (now - q[0]))
            q.append(now)
            if len(self._hits) > 10_000:  # 오래된 키 정리 (메모리 상한)
                for k in [k for k, v in self._hits.items() if not v or now - v[-1] >= self.window]:
                    del self._hits[k]
            return 0.0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


upload_limiter = SlidingWindowLimiter(60.0)


def enforce(limiter: SlidingWindowLimiter, key: str, limit: int, what: str = "요청") -> None:
    retry = limiter.hit(key, limit)
    if retry:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"{what}이 너무 많습니다. {int(retry) + 1}초 후 다시 시도해 주세요.",
            headers={"Retry-After": str(int(retry) + 1)},
        )
