#!/bin/bash
# 이 PC(개발)의 .env 에 메일 발송(SMTP)을 설정한다 — 설정하지 않으면 메일은 실제로 가지 않고 backend/logs 에만 남는다.
# 앱 비밀번호는 화면에 보이지 않게 입력받아 .env 에만 쓴다 (출력 · 기록 없음).
#
#   bash scripts/set_smtp_local.sh                       # Gmail (기본)
#   SMTP_HOST=smtp.naver.com SMTP_PORT=465 SMTP_SSL=true bash scripts/set_smtp_local.sh   # 네이버 등
#
# 보내는 계정(SMTP_USER)이 Gmail 이어도 **받는 사람은 어떤 메일(네이버 · 다음 · 회사 메일 …)이든** 된다.
# 끝나면 백엔드를 다시 시작해야 반영된다.
set -e
cd "$(dirname "$0")/.."
HOST="${SMTP_HOST:-smtp.gmail.com}"
PORT="${SMTP_PORT:-587}"
SSL="${SMTP_SSL:-false}"
# .env 에 SMTP_USER 가 이미 있으면 그 계정을 쓰고 비밀번호만 묻는다
ADDR="$(grep -E '^SMTP_USER=' .env 2>/dev/null | head -1 | cut -d= -f2-)"
if [ -z "$ADDR" ]; then read -r -p "보내는 메일 주소(SMTP 로그인 계정): " ADDR; else echo "보내는 계정: $ADDR (.env 의 SMTP_USER)"; fi
echo "앱 비밀번호(Gmail 은 16자)를 붙여넣고 Enter — 입력은 화면에 보이지 않습니다."
read -r -s -p "앱 비밀번호: " PW; echo
PW="${PW// /}"
[ -n "$PW" ] || { echo "비밀번호가 비어 있습니다."; exit 1; }
python - "$ADDR" "$PW" "$HOST" "$PORT" "$SSL" <<"PY"
import re, sys
from pathlib import Path
addr, pw, host, port, ssl = sys.argv[1:6]
p = Path(".env"); s = p.read_text(encoding="utf-8") if p.exists() else ""
def put(s, k, v):
    if re.search(rf"(?m)^{k}=", s):
        return re.sub(rf"(?m)^{k}=.*$", lambda m: f"{k}={v}", s, count=1)
    return s.rstrip("\n") + f"\n{k}={v}\n"
for k, v in {"SMTP_HOST": host, "SMTP_PORT": port, "SMTP_USER": addr, "SMTP_PASSWORD": pw,
             "SMTP_FROM": f"Cut & Keep <{addr}>", "SMTP_STARTTLS": "false" if ssl == "true" else "true", "SMTP_SSL": ssl}.items():
    s = put(s, k, v)
p.write_text(s, encoding="utf-8")
PY
unset PW
echo "저장됨 (.env). 백엔드를 다시 시작하면 가입 인증 · 아이디 찾기 · 비밀번호 재설정 메일이 실제로 갑니다."
