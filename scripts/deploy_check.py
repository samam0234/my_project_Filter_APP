#!/usr/bin/env python3
"""배포 리허설 점검 — 실제 도메인에 올린 서비스를 밖에서 확인하고(remote), 서버 안에서 확인한다(server).

  remote URL   밖에서 (아무 PC): 인증서 유효 · 만료 여유, http → https, 보안 헤더, 서버 버전 숨김, /health,
               약관 화면, 백엔드 API 문서 비노출, 로그인 없는 요청 거절, 다른 출처 CORS 거절
  server       서버 안 (저장소 폴더): APP_ENV=production · 비밀 키 · SMTP · 쿠키 Secure, 모델 파일(목록 · 체크섬),
               MariaDB 백업 최신 여부, Docker 서비스 상태

통과 ✓ · 경고 ! · 실패 ✗ 로 보여 주고, 실패가 있으면 종료 코드 1.
실행: python scripts/deploy_check.py remote https://example.com
      python scripts/deploy_check.py remote https://localhost --insecure   # 로컬 리허설 (DOMAIN 없이 HTTPS 오버레이)
      python scripts/deploy_check.py server [--models-manifest models.sha256.json]
"""

from __future__ import annotations

import argparse
import json
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CERT_MIN_DAYS = 14
BACKUP_MAX_HOURS = 26  # 24시간마다 백업 + 여유


class Report:
    def __init__(self) -> None:
        self.fails = 0
        self.warns = 0

    def ok(self, msg: str) -> None:
        print(f"  ✓ {msg}")

    def warn(self, msg: str) -> None:
        self.warns += 1
        print(f"  ! {msg}")

    def fail(self, msg: str) -> None:
        self.fails += 1
        print(f"  ✗ {msg}")

    def check(self, cond: bool, good: str, bad: str, warn_only: bool = False) -> bool:
        if cond:
            self.ok(good)
        elif warn_only:
            self.warn(bad)
        else:
            self.fail(bad)
        return cond


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):  # noqa: D401 — 리디렉트를 따라가지 않고 응답 그대로
        return None


_SSL_CTX: ssl.SSLContext | None = None  # --insecure 면 검증 안 하는 컨텍스트 (로컬 자체 서명 리허설용)


def _get(url: str, *, headers: dict | None = None, follow: bool = True, timeout: float = 15.0):
    """(status, headers, body bytes). 오류 응답도 그대로, 접속 실패는 (0, {}, b"")."""
    req = urllib.request.Request(url, headers={"User-Agent": "cutnkeep-deploy-check", **(headers or {})})
    handlers = [urllib.request.HTTPSHandler(context=_SSL_CTX)] if _SSL_CTX else []
    if not follow:
        handlers.append(_NoRedirect)
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(req, timeout=timeout) as r:
            return r.status, r.headers, r.read(200_000)
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read(200_000) if e.fp else b""
    except (urllib.error.URLError, OSError) as e:
        print(f"    (접속 실패 {url}: {getattr(e, 'reason', e)})")
        return 0, {}, b""


def cert_days_left(host: str, port: int = 443) -> float:
    ctx = ssl.create_default_context()  # 체인 · 호스트 이름 검증 (실패하면 예외)
    with socket.create_connection((host, port), timeout=10) as sock, ctx.wrap_socket(sock, server_hostname=host) as s:
        cert = s.getpeercert()
    expires = datetime.strptime(cert["notAfter"], "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    return (expires - datetime.now(timezone.utc)).total_seconds() / 86400


def remote(url: str, insecure: bool = False) -> Report:
    global _SSL_CTX
    rep = Report()
    u = urlparse(url if "://" in url else f"https://{url}")
    host, base = u.hostname, f"{u.scheme}://{u.netloc}"
    print(f"[remote] {base}")
    if insecure:
        _SSL_CTX = ssl.create_default_context()
        _SSL_CTX.check_hostname = False
        _SSL_CTX.verify_mode = ssl.CERT_NONE

    if u.scheme != "https":
        rep.fail("HTTPS 가 아님 — 공개 배포는 docker-compose.https.yml(Caddy)로 (아래는 http 로 나머지만 점검)")
    else:
        print("인증서")
        try:
            days = cert_days_left(host, u.port or 443)
            rep.check(days >= CERT_MIN_DAYS, f"유효, 만료까지 {days:.0f}일", f"만료까지 {days:.0f}일 — 갱신 확인 (Caddy 는 30일 전에 자동 갱신)")
        except ssl.SSLCertVerificationError as e:
            msg = f"인증서 검증 실패: {e.verify_message} — 자체 서명(DOMAIN 미설정)이거나 DNS 가 이 서버를 가리키지 않음"
            rep.warn(msg + " (--insecure 로 계속)") if insecure else rep.fail(msg)
            if not insecure:
                return rep
        except OSError as e:
            rep.fail(f"443 접속 실패: {e}")
            return rep

        print("http → https")
        st, hd, _ = _get(f"http://{host}/", follow=False)
        loc = hd.get("Location", "") if hd else ""
        if st == 0:
            rep.warn("80 접속 실패 — 방화벽에서 80 을 막았다면 인증서 갱신(HTTP-01)도 실패한다")
        else:
            rep.check(st in (301, 302, 307, 308) and loc.startswith("https://"), f"{st} → {loc}", f"http 가 https 로 넘어가지 않음 ({st} {loc})")

    print("첫 화면 · 보안 헤더")
    st, hd, body = _get(base + "/")
    rep.check(st == 200, "200", f"첫 화면 {st}")
    rep.check("max-age=" in (hd.get("Strict-Transport-Security") or ""), "HSTS", "HSTS 헤더 없음")
    rep.check(bool(hd.get("Content-Security-Policy")), "CSP", "Content-Security-Policy 없음")
    rep.check((hd.get("X-Frame-Options") or "").upper() == "DENY", "X-Frame-Options DENY", "X-Frame-Options 없음")
    rep.check((hd.get("X-Content-Type-Options") or "").lower() == "nosniff", "nosniff", "X-Content-Type-Options 없음")
    server = hd.get("Server") or ""
    rep.check(not any(ch.isdigit() for ch in server), f"서버 버전 숨김 ({server or '헤더 없음'})", f"Server 헤더에 버전 노출: {server}")

    print("API")
    st, hd, body = _get(base + "/health")
    try:
        health = json.loads(body)
    except ValueError:
        health = {}
    rep.check(st == 200 and health.get("status") == "ok", f"/health ok (버전 {health.get('version')})", f"/health {st}")
    rep.check(health.get("db_dialect") == "mysql", "서비스 DB MariaDB", f"서비스 DB {health.get('db_dialect')} — Docker 는 DOCKER_DB_DIALECT=mariadb 권장", warn_only=True)
    st, _, body = _get(base + "/api/v1/auth/me")
    rep.check(st == 401, "로그인 없는 /auth/me → 401", f"로그인 없는 /auth/me → {st}")
    st, _, body = _get(base + "/docs")
    rep.check(b"swagger" not in body.lower(), "API 문서(/docs) 비노출", "백엔드 Swagger 문서가 밖으로 열려 있음")
    st, hd, _ = _get(base + "/health", headers={"Origin": "https://evil.example"})
    acao = hd.get("Access-Control-Allow-Origin") if hd else None
    rep.check(acao not in ("*", "https://evil.example"), "다른 출처 CORS 거절", f"CORS 가 다른 출처를 허용함 ({acao})")

    print("약관 · 처리방침")
    for path in ("/privacy", "/terms"):
        st, _, _ = _get(base + path)
        rep.check(st == 200, f"{path} 200", f"{path} {st}")
    return rep


def _env(path: Path) -> dict[str, str]:
    out = {}
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def server(args) -> Report:
    import hashlib

    rep = Report()
    env_path = Path(args.env_file) if args.env_file else ROOT / ".env"
    env = _env(env_path if env_path.is_absolute() else ROOT / env_path)
    print(f"[server] {ROOT} · {env_path.name}")

    print(".env")
    if not env:
        rep.fail(".env 없음")
    rep.check(env.get("APP_ENV") == "production", "APP_ENV=production (위험한 설정이면 백엔드가 기동을 거부)", "APP_ENV 가 production 이 아님")
    key = env.get("SECRET_KEY", "")
    rep.check(len(key) >= 32 and "change" not in key, "SECRET_KEY 충분히 김", "SECRET_KEY 가 짧거나 기본값")
    rep.check(bool(env.get("SMTP_HOST")) and "mailpit" not in env.get("SMTP_HOST", ""), f"SMTP {env.get('SMTP_HOST')}", "SMTP 미설정 또는 개발용 Mailpit")
    rep.check(bool(env.get("DOMAIN")), f"DOMAIN={env.get('DOMAIN')}", "DOMAIN 없음 — Caddy 가 localhost 자체 서명 인증서를 쓴다")
    for k in ("OPERATOR_NAME", "OPERATOR_EMAIL"):
        rep.check(bool(env.get(k)), f"{k} 설정", f"{k} 없음 — 처리방침 · 약관에 운영자 정보가 비어 나온다", warn_only=True)

    print("모델 파일")
    backend = ROOT / "backend"
    wanted = {
        "YOLO_MODEL_PATH": env.get("YOLO_MODEL_PATH", "models/yolo26m-seg.pt"),
        "STUFF_MODEL_PATH": env.get("STUFF_MODEL_PATH", "models/segformer-ade.onnx"),
        "INPAINT_MODEL_PATH": env.get("INPAINT_MODEL_PATH", "models/lama_fp32.onnx"),
    }
    if env.get("LLM_PROVIDER", "ollama") == "lora" or env.get("LLM_FALLBACK") == "lora":
        wanted["LORA_ADAPTER_PATH"] = env.get("LORA_ADAPTER_PATH", "models/lora") + "/adapter_model.safetensors"
    for name, rel in wanted.items():
        p = (backend / rel) if not Path(rel).is_absolute() else Path(rel)
        if name == "INPAINT_MODEL_PATH" and not p.is_file():
            rep.warn(f"{rel} 없음 — MODEL_AUTO_DOWNLOAD 가 켜져 있으면 기동 후 받는다 (python scripts/fetch_models.py)")
            continue
        rep.check(p.is_file(), f"{rel} ({p.stat().st_size / 1e6:.0f}MB)" if p.is_file() else rel, f"{name}: {rel} 없음")
    if args.models_manifest:
        manifest = json.loads(Path(args.models_manifest).read_text(encoding="utf-8"))
        for rel, digest in manifest["files"].items():
            p = ROOT / rel
            if not p.is_file():
                rep.fail(f"체크섬 대상 없음: {rel}")
                continue
            h = hashlib.sha256()
            with p.open("rb") as f:
                for chunk in iter(lambda: f.read(1 << 20), b""):
                    h.update(chunk)
            rep.check(h.hexdigest() == digest, f"체크섬 일치 {rel}", f"체크섬 불일치 {rel} — 복사 중 깨졌거나 다른 버전")

    if args.gpu:
        print("GPU (docker-compose.gpu.yml)")
        base = Path(env.get("LORA_BASE_DIR") or ROOT / "training" / "models" / "qwen2.5-1.5b-instruct")
        base = base if base.is_absolute() else ROOT / base
        rep.check((base / "model.safetensors").is_file() and (base / "config.json").is_file(),
                  f"LoRA 베이스 모델 {base.relative_to(ROOT) if base.is_relative_to(ROOT) else base}", f"LoRA 베이스 모델 없음: {base} (LORA_BASE_DIR)")
        rep.check((backend / "models" / "lora" / "adapter_model.safetensors").is_file(), "LoRA 어댑터 backend/models/lora", "LoRA 어댑터 없음: backend/models/lora")
        probe = ("import torch,os;print(torch.cuda.is_available(), os.environ.get('LLM_PROVIDER'), "
                 "torch.cuda.get_device_name(0) if torch.cuda.is_available() else '')")
        try:
            out = subprocess.run(["docker", "compose", "-p", "cut_and_keep", "exec", "-T", "backend", "python", "-c", probe], cwd=ROOT,
                                 capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=60)
            line = (out.stdout or "").strip().splitlines()[-1:] or [""]
            parts = line[0].split(" ", 2)
            rep.check(parts[:1] == ["True"], f"컨테이너 CUDA 사용 가능 ({parts[2] if len(parts) > 2 else ''})",
                      f"컨테이너에서 CUDA 를 못 씀 ({(out.stderr or line[0]).strip()[:120]}) — NVIDIA Container Toolkit · -f docker-compose.gpu.yml 확인")
            rep.check(len(parts) > 1 and parts[1] == "lora", "문장 해석 LLM_PROVIDER=lora", f"LLM_PROVIDER={parts[1] if len(parts) > 1 else '?'} — GPU 오버레이가 아닌 듯", warn_only=True)
        except (OSError, subprocess.TimeoutExpired) as e:
            rep.warn(f"컨테이너 확인 못 함: {e}")

    print("백업")
    backups = sorted((ROOT / "data" / "mariaDB_backups").glob("*.sql.gz"), key=lambda p: p.stat().st_mtime)
    if not backups:
        rep.fail("data/mariaDB_backups 에 백업 없음 — mariadb-backup 서비스가 돌고 있나?")
    else:
        age = (time.time() - backups[-1].stat().st_mtime) / 3600
        rep.check(age <= BACKUP_MAX_HOURS, f"최근 백업 {age:.1f}시간 전 ({backups[-1].name})", f"최근 백업이 {age:.0f}시간 전 — 백업이 멈췄을 수 있음")

    print("Docker")
    try:
        out = subprocess.run(["docker", "compose", "-p", "cut_and_keep", "ps", "--format", "json"], cwd=ROOT,
                             capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30)
        stdout = out.stdout or ""
        rows = [json.loads(l) for l in stdout.splitlines() if l.strip().startswith("{")] if out.returncode == 0 else []
        if not rows and stdout.strip().startswith("["):
            rows = json.loads(stdout)
        if not rows:
            rep.fail("docker compose 서비스가 없음 (-p cut_and_keep)")
        for r in rows:
            name, state, health = r.get("Service"), r.get("State"), r.get("Health") or ""
            rep.check(state == "running" and health in ("", "healthy"), f"{name} {state} {health}".strip(), f"{name} {state} {health}".strip())
        names = {r.get("Service") for r in rows}
        for need in ("caddy", "mariadb-backup"):
            rep.check(need in names, f"{need} 실행 중", f"{need} 없음 — HTTPS 오버레이(docker-compose.https.yml) · 백업 서비스 확인")
        for dev in ("adminer", "mailpit"):
            if dev in names:
                rep.warn(f"{dev} 실행 중 — 개발용 도구 (127.0.0.1 에만 열려 있지만 운영 서버에서는 내리는 편이 낫다)")
    except (OSError, subprocess.TimeoutExpired) as e:
        rep.warn(f"docker 확인 못 함: {e}")
    return rep


def main() -> int:
    ap = argparse.ArgumentParser(description="배포 리허설 점검")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("remote")
    r.add_argument("url")
    r.add_argument("--insecure", action="store_true", help="인증서 검증 실패를 경고로 (로컬 자체 서명 리허설)")
    s = sub.add_parser("server")
    s.add_argument("--models-manifest", help="scripts/models_bundle.py 가 만든 체크섬 목록")
    s.add_argument("--env-file", help="점검할 env 파일 (기본 .env — 예: .env.production)")
    s.add_argument("--gpu", action="store_true", help="GPU 서버(docker-compose.gpu.yml) — LoRA 베이스 · 어댑터 · 컨테이너 CUDA 확인")
    args = ap.parse_args()
    rep = remote(args.url, args.insecure) if args.cmd == "remote" else server(args)
    print(f"\n실패 {rep.fails} · 경고 {rep.warns}")
    return 1 if rep.fails else 0


if __name__ == "__main__":
    sys.exit(main())
