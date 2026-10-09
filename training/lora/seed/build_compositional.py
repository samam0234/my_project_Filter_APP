#!/usr/bin/env python3
"""조합형 학습 문장 생성기 → seed/train_compositional.jsonl (결정적).

2026-10-08 재학습 뒤 LoRA 가 처음 보는 문장에서 틀린 유형을 정답 규칙이 정해진 틀로 넓힌다.
  1) 대상 둘 ("A랑 B만 남기고", "A랑 B 빼고 전부") — 하나를 빠뜨림
  2) 방해물 ("D는 두고 T만") — 시드에 있던 23개 어휘 밖(소 · 산 · 꽃병 …)에서 대상을 바꿈
  3) 관계 표현 ("R 옆의 T", "R 앞에 서 있는 T", "R 위의 T", "R 탄 T") — 위치 selector 로 오해 → selector 없음이 정답
  4) "오려내 · 잘라내" = 자르기, "남기고 크롭까지" = 배경 제거 + crop
  5) 어휘 — COCO · 배경 덩어리 거의 전부를 한국어 · 영어 이름으로

정답 규칙은 기존 시드 · 평가셋과 같다 (build_seed.py · eval*.jsonl):
  남기고 · 빼고 전부 · 투명하게 · 날려 → remove_bg [남길 것]
  지워줘(대상을 직접) → remove_object [지울 것]
  선명하게 · 빼고 블러 · X만 흐리게 → blur [X]
  오려 · 잘라 · 크롭 → crop, crop=true
평가셋 문장과 같은 문장은 학습 단계(dataset.py)에서 다시 한 번 뺀다.

실행: python training/lora/seed/build_compositional.py [--n 900]
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

HERE = Path(__file__).resolve().parent

# (한국어 이름들, 영어 이름들, 규격 라벨)
VOCAB: list[tuple[tuple[str, ...], tuple[str, ...], str]] = [
    (("사람", "남자", "여자", "아이"), ("person", "man", "woman", "kid"), "person"),
    (("자전거",), ("bicycle", "bike"), "bicycle"),
    (("자동차", "차"), ("car",), "car"),
    (("오토바이",), ("motorcycle", "motorbike"), "motorcycle"),
    (("비행기",), ("airplane", "plane"), "airplane"),
    (("버스",), ("bus",), "bus"),
    (("기차",), ("train",), "train"),
    (("트럭",), ("truck",), "truck"),
    (("보트", "배"), ("boat",), "boat"),
    (("신호등",), ("traffic light",), "traffic light"),
    (("소화전",), ("fire hydrant",), "fire hydrant"),
    (("정지 표지판",), ("stop sign",), "stop sign"),
    (("벤치",), ("bench",), "bench"),
    (("새",), ("bird",), "bird"),
    (("고양이",), ("cat",), "cat"),
    (("강아지", "개"), ("dog",), "dog"),
    (("말",), ("horse",), "horse"),
    (("양",), ("sheep",), "sheep"),
    (("소",), ("cow",), "cow"),
    (("코끼리",), ("elephant",), "elephant"),
    (("곰",), ("bear",), "bear"),
    (("얼룩말",), ("zebra",), "zebra"),
    (("기린",), ("giraffe",), "giraffe"),
    (("백팩", "배낭"), ("backpack",), "backpack"),
    (("우산",), ("umbrella",), "umbrella"),
    (("가방", "핸드백"), ("handbag", "bag"), "handbag"),
    (("넥타이",), ("tie",), "tie"),
    (("캐리어", "여행가방"), ("suitcase",), "suitcase"),
    (("연",), ("kite",), "kite"),
    (("스케이트보드",), ("skateboard",), "skateboard"),
    (("서핑보드",), ("surfboard",), "surfboard"),
    (("테니스 라켓",), ("tennis racket",), "tennis racket"),
    (("병", "물병"), ("bottle",), "bottle"),
    (("와인잔",), ("wine glass",), "wine glass"),
    (("컵", "머그컵"), ("cup", "mug"), "cup"),
    (("포크",), ("fork",), "fork"),
    (("칼",), ("knife",), "knife"),
    (("숟가락",), ("spoon",), "spoon"),
    (("그릇",), ("bowl",), "bowl"),
    (("바나나",), ("banana",), "banana"),
    (("사과",), ("apple",), "apple"),
    (("오렌지",), ("orange",), "orange"),
    (("브로콜리",), ("broccoli",), "broccoli"),
    (("당근",), ("carrot",), "carrot"),
    (("피자",), ("pizza",), "pizza"),
    (("도넛",), ("donut",), "donut"),
    (("케이크",), ("cake",), "cake"),
    (("의자",), ("chair",), "chair"),
    (("소파",), ("couch", "sofa"), "couch"),
    (("화분",), ("potted plant", "plant"), "potted plant"),
    (("침대",), ("bed",), "bed"),
    (("식탁", "테이블"), ("dining table", "table"), "dining table"),
    (("변기",), ("toilet",), "toilet"),
    (("티비", "TV"), ("tv",), "tv"),
    (("노트북",), ("laptop",), "laptop"),
    (("마우스",), ("mouse",), "mouse"),
    (("리모컨",), ("remote",), "remote"),
    (("키보드",), ("keyboard",), "keyboard"),
    (("휴대폰", "핸드폰"), ("cell phone", "phone"), "cell phone"),
    (("전자레인지",), ("microwave",), "microwave"),
    (("오븐",), ("oven",), "oven"),
    (("냉장고",), ("refrigerator", "fridge"), "refrigerator"),
    (("책",), ("book",), "book"),
    (("시계",), ("clock",), "clock"),
    (("꽃병",), ("vase",), "vase"),
    (("가위",), ("scissors",), "scissors"),
    (("곰인형",), ("teddy bear",), "teddy bear"),
    (("칫솔",), ("toothbrush",), "toothbrush"),
    # 배경 덩어리
    (("건물", "빌딩", "집"), ("building", "house"), "building"),
    (("하늘",), ("sky",), "sky"),
    (("도로", "차도"), ("road", "street"), "road"),
    (("인도", "보도"), ("sidewalk",), "sidewalk"),
    (("나무", "숲"), ("tree", "trees"), "tree"),
    (("잔디", "풀밭", "잔디밭"), ("grass", "lawn"), "grass"),
    (("바다", "호수", "강", "물"), ("water", "sea", "lake"), "water"),
    (("산", "언덕"), ("mountain", "hill"), "mountain"),
    (("벽",), ("wall",), "wall"),
    (("바닥",), ("floor",), "floor"),
    (("모래", "땅"), ("sand", "ground"), "ground"),
    (("울타리",), ("fence",), "fence"),
]
# 관계 표현에서 기준으로 쓰기 좋은 것 (장소 · 큰 물체)
ANCHORS = {"bench", "car", "bus", "tree", "building", "dining table", "couch", "bed", "fence", "wall", "road",
           "water", "train", "truck", "chair", "refrigerator", "tv", "bicycle", "horse", "person"}


def _batchim(word: str) -> bool:
    ch = word.strip()[-1]
    if "가" <= ch <= "힣":
        return (ord(ch) - 0xAC00) % 28 != 0
    return ch.lower() in "lmnr"  # TV 등 영문 끝 — 대충 맞춘다


def j(word: str, pair: str) -> str:
    """조사 붙이기. pair = "은는" · "이가" · "을를" · "과와" · "이랑랑"(이랑/랑) · "으로로"."""
    if pair == "이랑":
        return word + ("이랑" if _batchim(word) else "랑")
    a, b = pair[0], pair[1]
    return word + (a if _batchim(word) else b)


def P(target, effect="remove_bg", crop=False):
    return {"target": list(target), "effect": effect, "intensity": 15, "crop": crop, "selector": None}


def build(n: int, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)
    labels = [v[2] for v in VOCAB]
    ko = {v[2]: v[0] for v in VOCAB}
    en = {v[2]: v[1] for v in VOCAB}

    def pick(k: int, exclude=()):
        pool = [x for x in labels if x not in exclude]
        return rng.sample(pool, k)

    K = lambda lab: rng.choice(ko[lab])  # noqa: E731
    E = lambda lab: rng.choice(en[lab])  # noqa: E731

    def multi():
        a, b = pick(2)
        ka, kb = K(a), K(b)
        d = pick(1, (a, b))[0]
        kd = K(d)
        t = rng.choice([
            (f"{j(ka, '이랑')} {kb}만 남기고 나머지는 지워줘", P([a, b])),
            (f"{j(ka, '과와')} {j(kb, '은는')} 남기고 배경 없애줘", P([a, b])),
            (f"{j(ka, '이랑')} {kb} 빼고 전부 지워줘", P([a, b])),
            (f"{j(ka, '이랑')} {kb} 빼고 다 투명하게 해줘", P([a, b])),
            (f"{j(ka, '이랑')} {j(kb, '은는')} 살리고 {j(kd, '은는')} 지워줘", P([a, b])),
            (f"{j(ka, '이랑')} {j(kb, '은는')} 남기고 {j(kd, '은는')} 투명하게", P([a, b])),
            (f"{j(ka, '이랑')} {kb}만 선명하게 하고 나머지는 흐리게", P([a, b], "blur")),
            (f"{j(ka, '이랑')} {kb} 빼고 전부 블러", P([a, b], "blur")),
            (f"배경 날려줘 {j(ka, '이랑')} {j(kb, '은는')} 살려서", P([a, b])),
            (f"{j(ka, '이랑')} {j(kb, '을를')} 지워줘", P([a, b], "remove_object")),
            (f"{j(ka, '과와')} {kb} 둘 다 지워 주세요", P([a, b], "remove_object")),
            (f"keep only the {E(a)} and the {E(b)}", P([a, b])),
            (f"remove everything except the {E(a)} and the {E(b)}", P([a, b])),
            (f"erase the {E(a)} and the {E(b)}", P([a, b], "remove_object")),
            (f"blur everything but the {E(a)} and {E(b)}", P([a, b], "blur")),
        ])
        return t

    def distractor():
        t, d = pick(2)
        kt, kd = K(t), K(d)
        return rng.choice([
            (f"{j(kd, '은는')} 두고 {kt}만 지워줘", P([t], "remove_object")),
            (f"{j(kd, '은는')} 그대로 두고 {kt}만 없애줘", P([t], "remove_object")),
            (f"{kt}만 지워줘 {j(kd, '은는')} 그대로", P([t], "remove_object")),
            (f"{j(kt, '은는')} 지워줘 {j(kd, '은는')} 그대로 두고", P([t], "remove_object")),
            (f"{j(kd, '은는')} 놔두고 {j(kt, '을를')} 없애줘", P([t], "remove_object")),
            (f"{kd} 말고 {kt}만 남겨줘", P([t])),
            (f"{kt}만 남기고 {j(kd, '은는')} 지워줘", P([t])),
            (f"{j(kd, '은는')} 필요 없고 {kt}만 남겨 주세요", P([t])),
            (f"{kt}만 크롭하고 {j(kd, '은는')} 제외", P([t], "crop", True)),
            (f"{kt}만 잘라줘 {j(kd, '은는')} 빼고", P([t], "crop", True)),
            (f"{j(kd, '은는')} 두고 {kt}만 흐리게", P([t], "blur")),
            (f"{kt}만 선명하게 {j(kd, '은는')} 흐리게 해줘", P([t], "blur")),
            (f"{kt} 빼고 전부 블러 {j(kd, '이가')} 있어도 상관없어", P([t], "blur")),
            (f"remove the {E(t)} but leave the {E(d)}", P([t], "remove_object")),
            (f"keep the {E(t)}, not the {E(d)}", P([t])),
            (f"crop the {E(t)} only, ignore the {E(d)}", P([t], "crop", True)),
        ])

    def relation():
        t = pick(1)[0]
        r = rng.choice([a for a in ANCHORS if a != t])
        kt, kr = K(t), K(r)
        return rng.choice([
            (f"{kr} 옆의 {kt}만 남겨줘", P([t])),
            (f"{kr} 옆에 있는 {kt}만 남기고 나머지 투명하게", P([t])),
            (f"{kr} 앞에 서 있는 {kt}만 남기고 배경 지워", P([t])),
            (f"{kr} 위의 {kt}만 오려줘", P([t], "crop", True)),
            (f"{kr} 위에 있는 {kt}만 잘라내 줘", P([t], "crop", True)),
            (f"{kr} 뒤에 있는 {kt} 좀 지워줄래", P([t], "remove_object")),
            (f"{kr} 근처의 {kt}만 선명하게 하고 배경 흐리게", P([t], "blur")),
            (f"{kr} 옆 {j(kt, '은는')} 지우지 말고 남겨줘", P([t])),
            (f"the {E(t)} next to the {E(r)}, keep only that", P([t])),
            (f"crop the {E(t)} on the {E(r)}", P([t], "crop", True)),
        ])

    def rider():
        r = rng.choice(["bicycle", "horse", "motorcycle", "skateboard", "surfboard"])
        kr = K(r)
        verb = {"bicycle": "탄", "horse": "탄", "motorcycle": "탄", "skateboard": "탄", "surfboard": "타는"}[r]
        return rng.choice([
            (f"{kr} {verb} 사람만 남기고 배경 없애줘", P(["person"])),
            (f"{kr} {verb} 아이만 선명하게 하고 나머지는 흐리게", P(["person"], "blur")),
            (f"{kr} {verb} 사람은 두고 {j(K(r), '을를')} 지워줘", P([r], "remove_object")),
            (f"{kr} {verb} 사람은 그대로 두고 도로만 흐리게", P(["road"], "blur")),
        ])

    def crop_words():
        t = pick(1)[0]
        kt = K(t)
        return rng.choice([
            (f"{kt}만 오려내 줘", P([t], "crop", True)),
            (f"{kt}만 오려내줘", P([t], "crop", True)),
            (f"{kt}만 잘라내줘", P([t], "crop", True)),
            (f"사진에서 {kt}만 잘라 주세요", P([t], "crop", True)),
            (f"{kt} 부분만 크롭해줘", P([t], "crop", True)),
            (f"{kt}만 남기고 크롭까지 해줘", P([t], "remove_bg", True)),
            (f"{kt}만 남기고 배경 지운 다음 잘라줘", P([t], "remove_bg", True)),
            (f"cut out the {E(t)}", P([t], "crop", True)),
        ])

    def vocab():
        t = pick(1)[0]
        kt = K(t)
        return rng.choice([
            (f"{kt}만 남겨줘", P([t])),
            (f"{kt} 빼고 배경 날려줘", P([t])),
            (f"{j(kt, '을를')} 지워줘", P([t], "remove_object")),
            (f"{kt} 좀 없애 주세요", P([t], "remove_object")),
            (f"{kt}만 선명하게 하고 배경 흐리게", P([t], "blur")),
            (f"{kt} 빼고 다 흐릿하게", P([t], "blur")),
            (f"{j(kt, '을를')} 제외한 모든 것을 투명하게", P([t])),
            (f"keep the {E(t)}", P([t])),
            (f"remove the {E(t)}", P([t], "remove_object")),
        ])

    makers = [(multi, 0.26), (distractor, 0.24), (relation, 0.16), (rider, 0.04), (crop_words, 0.12), (vocab, 0.18)]
    out, seen = [], set()
    while len(out) < n:
        maker = rng.choices([m for m, _ in makers], [w for _, w in makers])[0]
        prompt, parsed = maker()
        key = prompt.replace(" ", "").lower()
        if key in seen:
            continue
        seen.add(key)
        out.append({"prompt": prompt, "parsed_prompt": parsed})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=900)
    ap.add_argument("--out", type=Path, default=HERE / "train_compositional.jsonl")
    args = ap.parse_args()
    rows = build(args.n)
    evals = set()
    for f in HERE.glob("eval*.jsonl"):
        for line in f.open(encoding="utf-8"):
            if line.strip():
                evals.add(json.loads(line)["prompt"].replace(" ", "").lower())
    kept = [r for r in rows if r["prompt"].replace(" ", "").lower() not in evals]
    with args.out.open("w", encoding="utf-8") as f:
        for r in kept:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"{len(kept)}건 → {args.out} (평가셋과 같은 문장 {len(rows) - len(kept)}건 제외)")


if __name__ == "__main__":
    main()
