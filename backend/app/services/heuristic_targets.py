"""LLM 없이 문장에서 "대상"을 뽑는 키워드 파서 — 어휘 확장 + 역할(남길 것 / 뺄 것) 규칙.

이전 폴백은 대상을 5종(사람·개·고양이·차·가방)만 알았고 "X 말고 Y만" 같은 부정 표현을 몰라 언급한 물체를 모두 대상으로
잡았다(평가셋 143문장에서 대상 정확도 56.6%, 정답 ⊂ 예측인 "초과"가 26건). 여기서는

  1) 어휘: prompt_spec 의 별칭표(한국어·영어·풍경) + COCO 클래스 이름 + 아래 일상어 보강 → 정규 클래스
  2) 역할: 언급 뒤에 붙은 표지로 판정
       keep    "Y만", "Y 남기", "keep Y", "only Y"            → 대상
       erase   "Y 지워", "remove Y"                           → 지울 대상 (남기는 표지가 문장에 없을 때만 대상)
       except  "X 말고", "X 빼고", "X 제외", "ignore X"       → 다른 대상이 있으면 대상에서 제외
       and     쉼표·"랑/와/과/하고/그리고/and" 로 이어진 앞 언급은 뒤 언급의 역할을 물려받는다
  3) 아무 언급이 없으면 사람

완벽한 언어 이해가 아니라 LLM 이 꺼져 있을 때의 안전망이다. LLM 해석과의 비교는 scripts/experiments/parse_rounds.py.
"""

from __future__ import annotations

import re
from typing import Dict, List, Tuple

from app.services.prompt_spec import COCO_CLASSES, STUFF_CLASSES, TARGET_ALIASES

# 한국어 일상어 보강 (별칭표에 없는 것). 값은 정규 클래스.
_EXTRA: Dict[str, str] = {
    **dict.fromkeys(("사람", "사람들", "인물", "남자", "여자", "남성", "여성", "아이", "아기", "학생", "사람이", "모델", "여자분", "남자분", "분들"), "person"),
    **dict.fromkeys(("강아지", "강쥐", "멍멍이", "개", "댕댕이"), "dog"),
    **dict.fromkeys(("고양이", "냥이", "고양이들"), "cat"),
    **dict.fromkeys(("자동차", "승용차", "차량", "차"), "car"),
    **dict.fromkeys(("버스",), "bus"),
    **dict.fromkeys(("트럭",), "truck"),
    **dict.fromkeys(("자전거",), "bicycle"),
    **dict.fromkeys(("오토바이", "바이크"), "motorcycle"),
    **dict.fromkeys(("새", "참새", "비둘기"), "bird"),
    **dict.fromkeys(("말", "조랑말"), "horse"),
    **dict.fromkeys(("양",), "sheep"),
    **dict.fromkeys(("소", "젖소"), "cow"),
    **dict.fromkeys(("코끼리",), "elephant"),
    **dict.fromkeys(("곰",), "bear"),
    **dict.fromkeys(("의자",), "chair"),
    **dict.fromkeys(("소파",), "couch"),
    **dict.fromkeys(("침대",), "bed"),
    **dict.fromkeys(("테이블", "식탁", "탁자", "책상"), "dining table"),
    **dict.fromkeys(("병", "물병"), "bottle"),
    **dict.fromkeys(("컵", "머그컵", "머그잔", "잔"), "cup"),
    **dict.fromkeys(("노트북",), "laptop"),
    **dict.fromkeys(("휴대폰", "핸드폰", "스마트폰", "폰"), "cell phone"),
    **dict.fromkeys(("가방", "핸드백"), "handbag"),
    **dict.fromkeys(("백팩", "배낭"), "backpack"),
    **dict.fromkeys(("우산",), "umbrella"),
    **dict.fromkeys(("책",), "book"),
    **dict.fromkeys(("시계",), "clock"),
    **dict.fromkeys(("꽃병",), "vase"),
    **dict.fromkeys(("화분",), "potted plant"),
    **dict.fromkeys(("티비", "텔레비전", "모니터"), "tv"),
    **dict.fromkeys(("곰인형", "인형"), "teddy bear"),
    **dict.fromkeys(("공",), "sports ball"),
    **dict.fromkeys(("스케이트보드",), "skateboard"),
    **dict.fromkeys(("서핑보드",), "surfboard"),
    **dict.fromkeys(("바나나",), "banana"),
    **dict.fromkeys(("피자",), "pizza"),
    **dict.fromkeys(("바다", "호수", "강물", "수면", "냇물"), "water"),
    **dict.fromkeys(("산맥", "언덕"), "mountain"),
    **dict.fromkeys(("케이크",), "cake"),
}

_PARTICLES = "은는이가을를만도와과랑의에로"  # 한 글자 조사
_PARTICLE_WORDS = ("이랑", "하고", "에서", "한테", "처럼", "까지", "보다", "으로", "에게", "말고", "빼고", "제외")

_KEEP_VERB = re.compile(r"^\s*(?:[은는이가을를만]\s*)*(?:남기|남겨|남길|keep|only)")
_ONLY = re.compile(r"^\s*(?:[은는이가을를]\s*)?만(?![가-힣])")
_KEEP_MARK = re.compile(r"^\s*(?:[은는이가을를]\s*)?(?:만(?![가-힣])|남기|남겨|남길|keep|only)")
_ERASE_MARK = re.compile(r"(?:지워|지우|없애|없앤|제거|치워|삭제|remove|erase|delete)")
_EXCEPT_MARK = re.compile(
    r"^\s*(?:[은는이가을를도]\s*)?(?:말고|빼고|제외|빼\b|그대로|놔두|놔 두|두고|내버려|건드리지|except|excluding|without|ignore|ignoring)"
)
_PRE_KEEP = re.compile(r"\b(?:keep|retain|preserve|only|just)\b[^,.]*$")
_PRE_ERASE = re.compile(r"\b(?:remove|erase|delete|get rid of|take out)\b[^,.]*$")
_PRE_EXCEPT = re.compile(r"\b(?:ignore|ignoring|except|excluding|without|but not|not the|(?:don't|do not|dont) touch|leave)\b[^,.]*$")
_AND_JOIN = re.compile(r"^\s*(?:,|와|과|랑|이랑|하고|및|그리고|and|&|/)\s*(?:the\s+|a\s+|an\s+)?$")
_KEEP_INTENT = re.compile(r"(?:남기|남겨|남길|keep|only|배경|background|블러|blur|흐리|흐릿|뿌옇|흐림|크롭|crop|잘라|오려)")


# 한 글자 한국어 낱말 중 일상어와 겹치는 것(강도·산책·물건·벽돌…)은 별칭표에서 가져오지 않는다. 아래 허용 목록만 쓴다.
_ONE_CHAR_OK = {"개", "차", "새", "말", "양", "소", "곰", "공", "병", "컵", "책", "폰", "잔", "산", "벽", "물", "풀"}


def _surface_table() -> List[Tuple[str, str]]:
    table: Dict[str, str] = {}
    for name in COCO_CLASSES:
        table[name] = name
    for name in STUFF_CLASSES:
        table[name] = name
    for key, canon in TARGET_ALIASES.items():
        key = key.lower()
        if len(key) == 1 and not key.isascii() and key not in _ONE_CHAR_OK:
            continue
        table[key] = canon
    table.update(_EXTRA)
    return sorted(table.items(), key=lambda kv: -len(kv[0]))  # 긴 표현 먼저


_TABLE = _surface_table()


def _is_hangul(ch: str) -> bool:
    return "가" <= ch <= "힣"


def find_mentions(text: str) -> List[Tuple[int, int, str]]:
    """문장에서 (시작, 끝, 정규 클래스) 목록 — 겹치면 긴 표현 우선, 위치 순."""
    taken = [False] * len(text)
    found: List[Tuple[int, int, str]] = []
    for surface, canon in _TABLE:
        start = 0
        while True:
            i = text.find(surface, start)
            if i < 0:
                break
            j = i + len(surface)
            start = i + 1
            if any(taken[i:j]):
                continue
            # 경계: 앞은 한글·영문이 아니어야 하고, 뒤는 (영문 키워드는) 단어 끝, (한글 키워드는) 조사·공백·끝
            before = text[i - 1] if i > 0 else " "
            after = text[j] if j < len(text) else " "
            ascii_key = surface.isascii()
            if ascii_key:
                if before.isalpha() and before.isascii():
                    continue
                tail = text[j : j + 2]
                if after.isalpha() and after.isascii() and tail not in ("s ", "es"):
                    if not (after in "s" and (j + 1 >= len(text) or not text[j + 1].isalpha())):
                        continue
            else:
                if _is_hangul(before) and len(surface) == 1:
                    continue  # "자동차" 안의 "차" 같은 것
                if _is_hangul(after):
                    rest = text[j:]
                    if not (after in _PARTICLES or rest.startswith(_PARTICLE_WORDS)):
                        continue
                    if len(surface) == 1 and after in "이가" and j + 1 < len(text) and _is_hangul(text[j + 1]) and not text[j + 1] in _PARTICLES:
                        continue  # "차이" 같은 다른 낱말
            for k in range(i, j):
                taken[k] = True
            found.append((i, j, canon))
    return sorted(found)


def detect_targets(text: str) -> List[str]:
    """소문자 문장 → 대상 클래스 목록 (중복 없음, 언급 순). 언급이 없으면 ["person"]."""
    return analyze(text)[0]


def analyze(text: str) -> Tuple[List[str], bool]:
    """소문자 문장 → (대상 목록, 지우기 의도). 지우기 의도 = 대상 자체를 지워 달라는 요청 (remove_object)."""
    mentions = find_mentions(text)
    if not mentions:
        return ["person"], False

    spans = []
    for idx, (s, e, canon) in enumerate(mentions):
        end = mentions[idx + 1][0] if idx + 1 < len(mentions) else len(text)
        spans.append(text[e:end])

    roles: List[str] = []
    prefix_based: List[bool] = []  # 역할이 앞쪽 동사(keep/remove …)에서 왔나 — 영어는 "keep A and B" 로 뒤 언급에 이어진다
    for idx, span in enumerate(spans):
        head = span[:14]  # 언급 바로 뒤 표지만 본다 (뒤 절의 표지를 끌어오지 않게)
        clause = re.split(r"[.!?\n]|[,，]\s*(?=\S)", span)[0] if span else ""
        prev_end = mentions[idx - 1][1] if idx else 0
        before = text[prev_end : mentions[idx][0]]  # 이번 언급 바로 앞 (영어: "keep only the")
        pre = False
        only_erase = _ONLY.match(head) and _ERASE_MARK.search(clause) and not _KEEP_VERB.search(clause)
        if _EXCEPT_MARK.search(head) or _PRE_EXCEPT.search(before):
            role, pre = "except", not _EXCEPT_MARK.search(head)
        elif only_erase:
            role = "erase"  # "강아지만 지워줘" — 만 + 지우는 동사 = 지울 대상
        elif _KEEP_MARK.search(head) or _PRE_KEEP.search(before):
            role, pre = "keep", not _KEEP_MARK.search(head)
        elif _PRE_ERASE.search(before) or (_ERASE_MARK.search(clause) and not _KEEP_MARK.search(clause)):
            role, pre = "erase", bool(_PRE_ERASE.search(before))
        else:
            role = "neutral"
        roles.append(role)
        prefix_based.append(pre)
    # 이어진 언급은 뒤 언급의 역할을 물려받는다 ("강아지, 고양이만 남기고")
    for idx in range(len(roles) - 2, -1, -1):
        if roles[idx] == "neutral" and _AND_JOIN.match(spans[idx]):
            roles[idx] = roles[idx + 1]

    # "keep the car and the bus" — 앞 언급이 앞쪽 동사로 역할을 얻었고 접속어로 이어진 중립 언급은 그 역할을 물려받는다
    for idx in range(1, len(roles)):
        if roles[idx] == "neutral" and prefix_based[idx - 1] and roles[idx - 1] != "neutral" and _AND_JOIN.match(spans[idx - 1]):
            roles[idx], prefix_based[idx] = roles[idx - 1], True

    names = [m[2] for m in mentions]
    keep = [n for n, r in zip(names, roles) if r == "keep"]
    erase = [n for n, r in zip(names, roles) if r == "erase"]
    neutral = [n for n, r in zip(names, roles) if r == "neutral"]
    except_ = [n for n, r in zip(names, roles) if r == "except"]

    erase_intent = False
    if keep:
        picked = keep
    elif erase and not _KEEP_INTENT.search(text):
        picked = erase  # "강아지 지워줘" · "강아지만 지워줘" — 지울 대상이 곧 대상
        erase_intent = True
    elif neutral:
        picked = neutral
    elif except_:
        picked = except_  # "사람 빼고 다 지워줘" — 빼는 쪽이 남기는 대상
    else:
        picked = erase or except_ or ["person"]
    out: List[str] = []
    for n in picked:
        if n not in out:
            out.append(n)
    return (out or ["person"]), erase_intent
