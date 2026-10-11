"""메일 본문 템플릿 — 아이디 안내 · 비밀번호 재설정 코드 · 회원가입 인증.

메일 클라이언트(Gmail · 네이버 · Outlook)는 <style> 과 최신 CSS 를 잘 지원하지 않는다 → 표(table) 레이아웃 +
인라인 스타일만 쓴다. 글자색·배경은 다크 모드에서 뒤집혀도 읽히도록 대비를 충분히 둔다.
각 함수는 (제목, 일반 텍스트, HTML) 을 돌려준다 — 텍스트 본문은 HTML 을 못 여는 클라이언트용 대체 본문이다.
사용자 입력(이름 · 아이디)은 html.escape 로 치환한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from html import escape
from typing import Optional

BRAND = "#0284c7"  # frontend/tailwind.config.ts brand-600
BRAND_DARK = "#075985"  # brand-800
BRAND_SOFT = "#eef9ff"  # brand-50
INK = "#0f172a"
MUTED = "#64748b"
LINE = "#e2e8f0"
FONT = "'Pretendard','Apple SD Gothic Neo','Malgun Gothic','Noto Sans KR',Arial,sans-serif"


@dataclass(frozen=True)
class Mail:
    subject: str
    text: str
    html: str


def _button(label: str, url: str) -> str:
    # 일부 클라이언트는 <a> 의 padding 을 무시한다 → 칸(td)에 색을 칠하고 링크가 칸을 채우게 한다
    return (
        '<table role="presentation" cellspacing="0" cellpadding="0" border="0" style="margin:28px auto 4px;">'
        f'<tr><td align="center" bgcolor="{BRAND}" style="border-radius:12px;">'
        f'<a href="{escape(url, quote=True)}" target="_blank" '
        f'style="display:inline-block;padding:14px 32px;font-family:{FONT};font-size:15px;font-weight:700;'
        f'color:#ffffff;text-decoration:none;border-radius:12px;">{escape(label)}</a>'
        "</td></tr></table>"
    )


def _code_box(code: str, caption: str) -> str:
    return (
        f'<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" style="margin:24px 0 4px;">'
        f'<tr><td align="center" bgcolor="{BRAND_SOFT}" '
        f'style="border:1px solid #bce7ff;border-radius:14px;padding:22px 12px;">'
        f'<div style="font-family:{FONT};font-size:12px;color:{MUTED};letter-spacing:.04em;margin-bottom:10px;">{escape(caption)}</div>'
        f'<div style="font-family:\'SFMono-Regular\',Consolas,\'Courier New\',monospace;font-size:32px;font-weight:700;'
        f'letter-spacing:.18em;color:{BRAND_DARK};">{escape(code)}</div>'
        "</td></tr></table>"
    )


def _layout(*, preheader: str, title: str, intro: str, body_html: str, footnote: str) -> str:
    return f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="light only">
<title>{escape(title)}</title>
</head>
<body style="margin:0;padding:0;background:#f1f5f9;">
<div style="display:none;max-height:0;overflow:hidden;opacity:0;color:transparent;">{escape(preheader)}</div>
<table role="presentation" width="100%" cellspacing="0" cellpadding="0" border="0" bgcolor="#f1f5f9">
<tr><td align="center" style="padding:32px 12px;">
  <table role="presentation" width="560" cellspacing="0" cellpadding="0" border="0"
         style="width:100%;max-width:560px;background:#ffffff;border-radius:18px;overflow:hidden;border:1px solid {LINE};">
    <tr><td bgcolor="{BRAND_DARK}" style="padding:22px 32px;background:linear-gradient(135deg,{BRAND_DARK},{BRAND});">
      <span style="font-family:{FONT};font-size:20px;font-weight:800;color:#ffffff;letter-spacing:-.01em;">컷앤킵</span>
      <span style="font-family:{FONT};font-size:12px;color:#bce7ff;margin-left:8px;">Cut &amp; Keep</span>
    </td></tr>
    <tr><td style="padding:36px 32px 12px;font-family:{FONT};color:{INK};">
      <h1 style="margin:0 0 12px;font-size:22px;line-height:1.35;font-weight:800;color:{INK};">{escape(title)}</h1>
      <p style="margin:0;font-size:15px;line-height:1.7;color:#334155;">{intro}</p>
      {body_html}
    </td></tr>
    <tr><td style="padding:20px 32px 32px;font-family:{FONT};">
      <div style="border-top:1px solid {LINE};padding-top:18px;font-size:12.5px;line-height:1.7;color:{MUTED};">{footnote}</div>
    </td></tr>
  </table>
  <p style="font-family:{FONT};font-size:11.5px;line-height:1.6;color:#94a3b8;margin:16px 0 0;">
    이 메일은 컷앤킵에서 자동으로 보냈어요. 회신하지 않으셔도 됩니다.
  </p>
</td></tr>
</table>
</body>
</html>
"""


def _hello(name: Optional[str]) -> str:
    return f"{escape(name)}님, 안녕하세요." if name else "안녕하세요."


def _hello_text(name: Optional[str]) -> str:
    return f"{name}님, 안녕하세요." if name else "안녕하세요."


def signup_verify(*, code: str, verify_url: str, ttl_minutes: int, name: Optional[str] = None) -> Mail:
    subject = "[컷앤킵] 회원가입 인증 일련번호"
    text = (
        f"{_hello_text(name)}\n\n"
        "컷앤킵 가입을 이어가려면 아래 일련번호가 필요해요.\n\n"
        f"    일련번호: {code}\n\n"
        f"1) 아래 주소를 열고  2) 일련번호를 입력하면 가입이 끝나요. ({ttl_minutes}분 안에)\n"
        f"{verify_url}\n\n"
        "본인이 가입을 요청하지 않았다면 이 메일을 무시해 주세요. 아무것도 바뀌지 않습니다.\n"
    )
    html = _layout(
        preheader=f"일련번호 {code} — {ttl_minutes}분 안에 입력해 주세요",
        title="회원가입 인증",
        intro=f"{_hello(name)}<br>컷앤킵 가입을 이어가려면 아래 <b>일련번호</b>가 필요해요. "
        "버튼을 눌러 인증 화면을 열고, 이 일련번호를 입력해 주세요.",
        body_html=_code_box(code, "회원가입 일련번호") + _button("회원가입 인증", verify_url),
        footnote=f"일련번호는 <b>{ttl_minutes}분</b> 동안만 유효하고, 5번 틀리면 새로 받아야 해요.<br>"
        "본인이 가입을 요청하지 않았다면 이 메일을 무시해 주세요. 아무것도 바뀌지 않습니다.",
    )
    return Mail(subject, text, html)


def find_id(*, username: str, login_url: str, name: Optional[str] = None) -> Mail:
    subject = "[컷앤킵] 아이디 안내"
    text = (
        f"{_hello_text(name)}\n\n"
        f"요청하신 컷앤킵 아이디는 다음과 같습니다.\n\n    {username}\n\n"
        f"로그인: {login_url}\n\n"
        "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다.\n"
    )
    html = _layout(
        preheader="요청하신 컷앤킵 아이디를 알려 드려요",
        title="아이디 안내",
        intro=f"{_hello(name)}<br>요청하신 컷앤킵 아이디예요.",
        body_html=_code_box(username, "내 아이디").replace("letter-spacing:.18em", "letter-spacing:.04em")
        + _button("로그인하기", login_url),
        footnote="비밀번호가 기억나지 않으면 로그인 화면의 <b>비밀번호 찾기</b>를 이용해 주세요.<br>"
        "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다.",
    )
    return Mail(subject, text, html)


def password_reset(*, code: str, reset_url: str, ttl_minutes: int, name: Optional[str] = None) -> Mail:
    subject = "[컷앤킵] 비밀번호 재설정 인증 코드"
    text = (
        f"{_hello_text(name)}\n\n"
        f"비밀번호 재설정 인증 코드: {code}\n\n"
        f"{ttl_minutes}분 안에 아래 화면에서 입력해 주세요.\n{reset_url}\n\n"
        "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다. 비밀번호는 바뀌지 않습니다.\n"
    )
    html = _layout(
        preheader=f"인증 코드 {code} — {ttl_minutes}분 안에 입력해 주세요",
        title="비밀번호 재설정",
        intro=f"{_hello(name)}<br>비밀번호를 다시 정하려면 아래 <b>인증 코드</b>를 재설정 화면에 입력해 주세요.",
        body_html=_code_box(code, "인증 코드") + _button("재설정 화면 열기", reset_url),
        footnote=f"코드는 <b>{ttl_minutes}분</b> 동안만 유효해요. 비밀번호를 바꾸면 다른 기기는 모두 로그아웃돼요.<br>"
        "본인이 요청하지 않았다면 이 메일을 무시하셔도 됩니다. 비밀번호는 바뀌지 않습니다.",
    )
    return Mail(subject, text, html)
