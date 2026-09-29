#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""인스턴스 선택·물체 지우기 시드 학습 데이터 생성 (결정적, torch 불필요).

피드백·의사 라벨(data/pseudo_labels)은 "X만 크롭" 같은 단순 요청뿐이라
selector(위치·순서·개수·색 속성)와 remove_object 를 배울 예제가 없다.
여기서 한국어·영어 문장 템플릿 × 대상 × 조건을 조합해 정답이 확실한 쌍을 만든다.

출력: training/lora/seed/train.jsonl  ({"prompt", "parsed_prompt"} 한 줄씩)
평가셋 eval.jsonl 은 **손으로 쓴 다른 표현**이라 여기서 만들지 않는다 (일반화 측정용).

사용:
  python training/lora/seed/build_seed.py            # train.jsonl 갱신
  python training/lora/seed/build_seed.py --count 800
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

SEED_DIR = Path(__file__).resolve().parent

# (COCO 클래스, 한국어 표현들, 영어 표현, 셀 때 단위)
OBJECTS = [
    ("person", ["사람", "남자", "여자", "아이", "인물", "남성", "여성"], "person", "명"),
    ("dog", ["강아지", "개"], "dog", "마리"),
    ("cat", ["고양이"], "cat", "마리"),
    ("car", ["차", "자동차", "승용차"], "car", "대"),
    ("bus", ["버스"], "bus", "대"),
    ("bicycle", ["자전거"], "bicycle", "대"),
    ("motorcycle", ["오토바이"], "motorcycle", "대"),
    ("bird", ["새"], "bird", "마리"),
    ("horse", ["말"], "horse", "마리"),
    ("cup", ["컵", "머그컵"], "cup", "개"),
    ("bottle", ["병", "물병"], "bottle", "개"),
    ("chair", ["의자"], "chair", "개"),
    ("laptop", ["노트북"], "laptop", "대"),
    ("cell phone", ["휴대폰", "핸드폰", "폰"], "phone", "대"),
    ("handbag", ["가방", "핸드백"], "handbag", "개"),
]
PERSON = OBJECTS[0]

POSITIONS = [
    ("front", ["맨 앞에 있는", "제일 앞에 있는", "앞쪽", "맨 앞"], "front"),
    ("back", ["맨 뒤에 있는", "제일 뒤", "뒤쪽"], "back"),
    ("left", ["왼쪽에 있는", "왼쪽", "좌측"], "leftmost"),
    ("right", ["오른쪽에 있는", "오른쪽", "우측"], "rightmost"),
    ("center", ["가운데 있는", "가운데", "중앙에 있는"], "center"),
    ("largest", ["가장 큰", "제일 큰"], "biggest"),
    ("smallest", ["가장 작은", "제일 작은"], "smallest"),
]
SIDES = [("left", "왼쪽", "left"), ("right", "오른쪽", "right")]
ORDINALS = [(2, "두 번째", "second"), (3, "세 번째", "third"), (4, "네 번째", "fourth")]
COUNTS = [(2, "두"), (3, "세"), (2, "2"), (3, "3")]

COLORS = [
    ("red", ["빨간", "빨간색"]),
    ("blue", ["파란", "파란색"]),
    ("white", ["흰", "하얀", "흰색"]),
    ("black", ["검은", "검정"]),
    ("yellow", ["노란", "노란색"]),
    ("green", ["초록", "초록색"]),
    ("neon yellow", ["형광", "형광색"]),
    ("gray", ["회색"]),
    ("orange", ["주황색"]),
    ("pink", ["분홍색"]),
]
# (영어 부위, 한국어 부위, 착용 동사)
PARTS = [
    ("helmet", "안전모", "쓴"),
    ("hat", "모자", "쓴"),
    ("vest", "조끼", "입은"),
    ("shirt", "셔츠", "입은"),
    ("jacket", "자켓", "입은"),
    ("jacket", "점퍼", "입은"),
    ("hoodie", "후드티", "입은"),
    ("raincoat", "우비", "입은"),
    ("t-shirt", "티셔츠", "입은"),
    ("pants", "바지", "입은"),
]

KEEP_BG_KO = ["만 남기고 배경 지워줘", "만 남기고 배경 제거", "만 남기고 나머지 다 지워", "만 남겨줘",
              "만 남기고 배경 없애줘", "만 남기고 배경 투명하게", "만 남기고 배경은 투명하게 해줘",
              "만 살리고 나머지 지워", "만 누끼 따줘"]
KEEP_EXCEPT_KO = ["빼고 전부 지워줘", "제외하고 전부 제거해줘", "말고 다 지워", "빼고 배경 날려줘"]
BLUR_KO = ["만 남기고 배경 블러", "만 선명하게 하고 배경 흐리게", "만 남기고 배경 흐리게 해줘"]
CROP_KO = ["만 크롭해줘", "만 잘라줘", "만 오려내줘", "만 오려줘", "만 딱 맞게 잘라줘"]
REMOVE_KO = ["지워줘", "없애줘", "삭제해줘", "제거해줘", "지워 줘", "치워줘", "치워 줄래?", "안 보이게 지워줘"]
# 대상 언급 없이 배경만 말하는 요청 → 기본 대상 person
BACKGROUND_ONLY_KO = [
    ("배경 지워줘", "remove_bg"), ("배경을 투명하게 바꿔줘", "remove_bg"), ("배경 날려줘", "remove_bg"),
    ("배경 없애줘", "remove_bg"), ("배경만 흐리게", "blur"), ("배경 블러 처리", "blur"),
    ("배경만 뿌옇게 해줘", "blur"), ("누끼 따줘", "remove_bg"),
]

REMOVE_EN = ["remove the {x}", "erase the {x}", "delete the {x} from the photo", "get rid of the {x}"]
KEEP_EN = ["keep only the {x} and remove the background", "keep the {x}, remove everything else",
           "make the background transparent but keep the {x}"]
CROP_EN = ["crop out the {x}", "crop the image to the {x}", "crop around the {x}"]
BLUR_EN = ["keep the {x} sharp and blur the background", "blur everything except the {x}"]


def _batchim(word: str) -> bool:
    """마지막 글자에 받침이 있는지 (한글 아니면 False)."""
    ch = word.strip()[-1:]
    return bool(ch) and "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0


def josa(word: str, with_batchim: str, without: str) -> str:
    """받침에 맞는 조사 붙이기: josa("자켓", "을", "를") → "자켓을"."""
    return word + (with_batchim if _batchim(word) else without)


def label(target, effect="remove_bg", intensity=15, crop=False, position=None, rank=None,
          count=None, attributes=None) -> dict:
    selector = None
    if position or rank or count or attributes:
        selector = {"position": position, "rank": rank, "count": count,
                    "attributes": list(attributes or [])}
    return {"target": [target], "effect": effect, "intensity": intensity,
            "crop": crop or effect == "crop", "selector": selector}


def _obj(rng, person_bias=0.45):
    return PERSON if rng.random() < person_bias else rng.choice(OBJECTS[1:])


def _keep_effect(rng):
    """(한국어 꼬리, effect, intensity) — 남기기 계열 효과 하나."""
    kind = rng.random()
    if kind < 0.55:
        return rng.choice(KEEP_BG_KO), "remove_bg", 15
    if kind < 0.85:
        n = rng.choice([None, 20, 30, 40, 60])
        tail = rng.choice(BLUR_KO) + (f" 강도 {n}" if n else "")
        return tail, "blur", n or 15
    return rng.choice(CROP_KO), "crop", 15


def gen_plain(rng):
    """선택자 없음 — 전체 인스턴스 (기존 동작 유지 학습)."""
    if rng.random() < 0.15:
        text, effect = rng.choice(BACKGROUND_ONLY_KO)
        return text, label("person", effect)
    cls, kos, en, _ = _obj(rng)
    ko = rng.choice(kos)
    if rng.random() < 0.3:
        return f"{ko} {rng.choice(REMOVE_KO)}", label(cls, "remove_object")
    tail, effect, inten = _keep_effect(rng)
    return f"{ko}{tail}", label(cls, effect, inten)


def gen_position(rng):
    cls, kos, en, _ = _obj(rng)
    pos, pkos, pen = rng.choice(POSITIONS)
    ko = f"{rng.choice(pkos)} {rng.choice(kos)}"
    if rng.random() < 0.4:
        return f"{ko} {rng.choice(REMOVE_KO)}", label(cls, "remove_object", position=pos, count=1)
    tail, effect, inten = _keep_effect(rng)
    return f"{ko}{tail}", label(cls, effect, inten, position=pos, count=1)


def gen_rank(rng):
    cls, kos, en, _ = _obj(rng)
    side, side_ko, side_en = rng.choice(SIDES)
    n, n_ko, n_en = rng.choice(ORDINALS)
    ko = f"{side_ko}에서 {n_ko} {rng.choice(kos)}"
    if rng.random() < 0.5:
        return f"{ko} {rng.choice(REMOVE_KO)}", label(cls, "remove_object", position=side, rank=n, count=1)
    tail, effect, inten = _keep_effect(rng)
    return f"{ko}{tail}", label(cls, effect, inten, position=side, rank=n, count=1)


def gen_count(rng):
    cls, kos, en, unit = _obj(rng)
    n, n_ko = rng.choice(COUNTS)
    tail, effect, inten = _keep_effect(rng)
    if not tail.startswith("만"):
        tail = "만" + tail
    return f"{rng.choice(kos)} {n_ko}{unit}{tail}", label(cls, effect, inten, count=n)


def gen_attribute(rng):
    """색+부위(사람) 또는 색+사물."""
    color, cks = rng.choice(COLORS)
    if rng.random() < 0.65:
        part_en, part_ko, verb = rng.choice(PARTS)
        who = rng.choice(PERSON[1])
        ko = f"{rng.choice(cks)} {part_ko} {verb} {who}"
        attr, cls = f"{color} {part_en}", "person"
    else:
        cls, kos, en, _ = rng.choice([o for o in OBJECTS[1:] if o[0] in {"car", "bus", "bicycle", "cup", "handbag", "dog", "cat", "chair", "bottle"}])
        ko = f"{rng.choice(cks)} {rng.choice(kos)}"
        attr = f"{color} {cls if cls != 'handbag' else 'bag'}"
    if rng.random() < 0.4:
        return f"{ko} {rng.choice(REMOVE_KO)}", label(cls, "remove_object", attributes=[attr])
    tail, effect, inten = _keep_effect(rng)
    return f"{ko}{tail}", label(cls, effect, inten, attributes=[attr])


def gen_position_attribute(rng):
    """사용자 실제 사례 계열: 위치 + 색 속성 1~2개 + '빼고/제외하고 전부 지워'."""
    pos, pkos, _ = rng.choice(POSITIONS[:5])
    picks = rng.sample(PARTS, 2) if rng.random() < 0.5 else [rng.choice(PARTS)]
    attrs, phrases = [], []
    for part_en, part_ko, verb in picks:
        color, cks = rng.choice(COLORS)
        attrs.append(f"{color} {part_en}")
        phrases.append((f"{rng.choice(cks)} {part_ko}", verb))
    if len(phrases) == 2:
        desc = f"{josa(phrases[0][0], '과', '와')} {josa(phrases[1][0], '을', '를')} {phrases[1][1]}"
    else:
        desc = f"{phrases[0][0]} {phrases[0][1]}"
    who = rng.choice(["남자", "남성", "사람", "여자", "작업자"])
    base = f"{rng.choice(pkos)} {desc} {who}"
    r = rng.random()
    if r < 0.4:
        return f"{josa(base, '을', '를')} {rng.choice(KEEP_EXCEPT_KO)}", label("person", "remove_bg", position=pos, count=1, attributes=attrs)
    if r < 0.7:
        return f"{base} {rng.choice(REMOVE_KO)}", label("person", "remove_object", position=pos, count=1, attributes=attrs)
    tail, effect, inten = _keep_effect(rng)
    return f"{base}{tail}", label("person", effect, inten, position=pos, count=1, attributes=attrs)


def gen_english(rng):
    cls, kos, en, _ = _obj(rng)
    r = rng.random()
    if r < 0.3:
        pos, _, pen = rng.choice(POSITIONS)
        x = f"{pen} {en}"
        return rng.choice(REMOVE_EN).format(x=x), label(cls, "remove_object", position=pos, count=1)
    if r < 0.5:
        side, _, side_en = rng.choice(SIDES)
        n, _, n_en = rng.choice(ORDINALS)
        x = f"{n_en} {en} from the {side_en}"
        return rng.choice(KEEP_EN).format(x=x), label(cls, "remove_bg", position=side, rank=n, count=1)
    if r < 0.75:
        color, _ = rng.choice(COLORS)
        x = f"{color} {en}"
        attr = f"{color} {cls if cls != 'handbag' else 'bag'}"
        if rng.random() < 0.5:
            return rng.choice(REMOVE_EN).format(x=x), label(cls, "remove_object", attributes=[attr])
        return rng.choice(BLUR_EN).format(x=x), label(cls, "blur", attributes=[attr])
    if rng.random() < 0.3:
        pos, _, pen = rng.choice(POSITIONS)
        if rng.random() < 0.5:
            return rng.choice(CROP_EN).format(x=f"{pen} {en}"), label(cls, "crop", position=pos, count=1)
        return rng.choice(CROP_EN).format(x=en), label(cls, "crop")
    if rng.random() < 0.4:
        return rng.choice(BLUR_EN).format(x=en), label(cls, "blur")
    return rng.choice(KEEP_EN).format(x=en), label(cls, "remove_bg")


# 【수동·튜닝】 생성기 비율 — selector 계열을 넉넉히, plain 은 기존 동작 유지용
GENERATORS = [
    (gen_plain, 0.2),
    (gen_position, 0.18),
    (gen_rank, 0.12),
    (gen_count, 0.08),
    (gen_attribute, 0.16),
    (gen_position_attribute, 0.16),
    (gen_english, 0.14),
]


def build(count: int, seed: int = 42) -> list[dict]:
    rng = random.Random(seed)
    funcs, weights = zip(*GENERATORS)
    seen: set[str] = set()
    rows: list[dict] = []
    guard = 0
    while len(rows) < count and guard < count * 50:
        guard += 1
        prompt, parsed = rng.choices(funcs, weights)[0](rng)
        prompt = " ".join(prompt.split())
        if prompt in seen:
            continue
        seen.add(prompt)
        rows.append({"prompt": prompt, "parsed_prompt": parsed})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(description="LoRA 인스턴스 선택 시드 데이터 생성")
    parser.add_argument("--count", type=int, default=800)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--out", type=Path, default=SEED_DIR / "train.jsonl")
    args = parser.parse_args()

    rows = build(args.count, args.seed)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with_sel = sum(1 for r in rows if r["parsed_prompt"]["selector"])
    removes = sum(1 for r in rows if r["parsed_prompt"]["effect"] == "remove_object")
    print(f"{len(rows)} rows → {args.out}  (selector {with_sel}, remove_object {removes})")


if __name__ == "__main__":
    main()
