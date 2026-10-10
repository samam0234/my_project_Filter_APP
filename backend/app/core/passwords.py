"""비밀번호 해시 · 토큰 · 인증 코드 (표준 라이브러리만 사용).

- 비밀번호: hashlib.scrypt (메모리 하드 KDF) + 사용자별 16바이트 salt
  저장 형식: "scrypt$<n>$<r>$<p>$<salt_b64>$<hash_b64>" — 파라미터를 함께 저장해 나중에 올려도 호환
- 세션 토큰: secrets.token_urlsafe(32) 원문은 쿠키에만, DB 에는 SHA-256
- 재설정 코드: 6자리 숫자, DB 에는 HMAC-SHA256(SECRET_KEY, user_id:code)
- 비교는 모두 hmac.compare_digest (타이밍 공격 방지)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets

# 【수동·튜닝】 scrypt 비용 — n=2**14 는 요청당 약 50ms · 16MB (OWASP 권장 최소)
SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
_MAXMEM = 64 * 1024 * 1024

USERNAME_RE = re.compile(r"^[a-z0-9_]{4,20}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
PASSWORD_MIN = 8
PASSWORD_MAX = 64


def _b64(data: bytes) -> str:
    return base64.b64encode(data).decode("ascii")


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.scrypt(
        password.encode("utf-8"), salt=salt, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P, maxmem=_MAXMEM
    )
    return f"scrypt${SCRYPT_N}${SCRYPT_R}${SCRYPT_P}${_b64(salt)}${_b64(digest)}"


def verify_password(password: str, stored: str) -> bool:
    try:
        algo, n, r, p, salt_b64, hash_b64 = stored.split("$")
        if algo != "scrypt":
            return False
        expected = base64.b64decode(hash_b64)
        digest = hashlib.scrypt(
            password.encode("utf-8"),
            salt=base64.b64decode(salt_b64),
            n=int(n),
            r=int(r),
            p=int(p),
            maxmem=_MAXMEM,
            dklen=len(expected),
        )
    except (ValueError, TypeError):
        return False
    return hmac.compare_digest(digest, expected)


# 존재하지 않는 아이디로 로그인할 때도 같은 시간만큼 해시를 계산해
# 응답 시간으로 계정 존재 여부를 알 수 없게 한다.
DUMMY_HASH = hash_password(secrets.token_hex(16))


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_code() -> str:
    """6자리 숫자 (앞자리 0 포함)."""
    return f"{secrets.randbelow(1_000_000):06d}"


def code_digest(secret_key: str, user_id: str, code: str) -> str:
    return hmac.new(
        secret_key.encode("utf-8"), f"{user_id}:{code}".encode("utf-8"), hashlib.sha256
    ).hexdigest()


def password_problem(password: str) -> str | None:
    """비밀번호 규칙 위반 사유 (없으면 None). 8~64자, 영문과 숫자 각각 1개 이상."""
    if not PASSWORD_MIN <= len(password) <= PASSWORD_MAX:
        return f"비밀번호는 {PASSWORD_MIN}~{PASSWORD_MAX}자여야 합니다."
    if not re.search(r"[A-Za-z]", password) or not re.search(r"\d", password):
        return "비밀번호에 영문과 숫자를 모두 넣어 주세요."
    return None


def mask_email(email: str) -> str:
    """ab****@example.com — 안내 문구용."""
    local, _, domain = email.partition("@")
    keep = local[:2] if len(local) > 2 else local[:1]
    return f"{keep}{'*' * max(2, len(local) - len(keep))}@{domain}"
