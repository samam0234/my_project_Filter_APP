#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""실험: 동시 요청 부하 — 업로드 처리 지연·처리량·오류와 처리 중 /health 응답.

실서버(uvicorn)가 떠 있어야 한다. 비로그인 업로드라 DB·파일이 남지 않는다 (서비스 정책).
요청마다 프롬프트를 조금씩 바꿔 LLM 캐시 효과를 없앤다.

실행 (저장소 루트, training venv):
  python scripts/experiments/load_test.py --levels 1,2,4,8 --per-level 8
"""

from __future__ import annotations

import argparse
import asyncio
import json
import statistics
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
PROMPTS = [
    "사람만 남기고 배경 제거",
    "왼쪽에서 두 번째 사람 지워줘",
    "사람만 남기고 배경 블러 강도 40",
    "맨 오른쪽 사람만 남겨",
    "가운데 사람만 남기고 크롭",
    "제일 큰 사람만 선명하게 나머지 흐리게",
    "사람 두 명만 남기고 배경 투명",
    "오른쪽 사람 지워 줘",
]


def pct(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    values = sorted(values)
    k = min(len(values) - 1, max(0, round(q * (len(values) - 1))))
    return values[k]


async def health_probe(client: httpx.AsyncClient, stop: asyncio.Event, out: list[float]) -> None:
    while not stop.is_set():
        t = time.perf_counter()
        try:
            await client.get("/health", timeout=30)
            out.append((time.perf_counter() - t) * 1000)
        except httpx.HTTPError:
            out.append(float("inf"))
        await asyncio.sleep(0.5)


async def one(client: httpx.AsyncClient, image: bytes, prompt: str) -> tuple[float, str]:
    t = time.perf_counter()
    try:
        r = await client.post("/api/v1/upload", files={"file": ("a.jpg", image, "image/jpeg")},
                              data={"prompt": prompt}, timeout=600)
        status = r.json().get("status", str(r.status_code)) if r.status_code == 200 else f"http{r.status_code}"
    except httpx.HTTPError as exc:
        status = f"error:{type(exc).__name__}"
    return time.perf_counter() - t, status


async def level(base: str, image: bytes, concurrency: int, total: int) -> dict:
    async with httpx.AsyncClient(base_url=base) as client:
        stop = asyncio.Event()
        health: list[float] = []
        probe = asyncio.create_task(health_probe(client, stop, health))
        sem = asyncio.Semaphore(concurrency)

        async def run(i: int):
            async with sem:
                return await one(client, image, f"{PROMPTS[i % len(PROMPTS)]} ({i})")

        started = time.perf_counter()
        results = await asyncio.gather(*(run(i) for i in range(total)))
        wall = time.perf_counter() - started
        stop.set()
        await probe
    lat = [r[0] for r in results]
    statuses: dict[str, int] = {}
    for _, s in results:
        statuses[s] = statuses.get(s, 0) + 1
    ok_health = [h for h in health if h != float("inf")]
    return {
        "concurrency": concurrency, "requests": total, "wall_s": round(wall, 1),
        "throughput_per_min": round(total / wall * 60, 1),
        "latency_p50_s": round(statistics.median(lat), 2), "latency_p95_s": round(pct(lat, 0.95), 2),
        "latency_max_s": round(max(lat), 2), "statuses": statuses,
        "health_p50_ms": round(statistics.median(ok_health), 1) if ok_health else None,
        "health_max_ms": round(max(ok_health), 1) if ok_health else None,
        "health_failures": len(health) - len(ok_health),
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="http://127.0.0.1:8000")
    ap.add_argument("--levels", default="1,2,4,8")
    ap.add_argument("--per-level", type=int, default=8)
    ap.add_argument("--image", type=Path, default=None, help="기본: 검증 데이터셋의 사람 여러 명 사진")
    ap.add_argument("--report", type=Path, default=None)
    args = ap.parse_args()

    image_path = args.image or next(iter(sorted((ROOT / "training/datasets/cutnkeep_seg_5k/images/val").glob("*.jpg"))))
    image = image_path.read_bytes()
    httpx.get(args.base + "/health", timeout=10).raise_for_status()
    # 워밍업 1건 (모델 로드·LLM 로드 제외)
    asyncio.run(level(args.base, image, 1, 1))

    rows = []
    print(f"이미지 {image_path.name} ({len(image) // 1024} KB)")
    print(f"{'동시':>4}{'요청':>5}{'총 s':>7}{'건/분':>7}{'p50 s':>7}{'p95 s':>7}{'max s':>7}{'health p50':>12}{'health max':>12}  상태")
    for c in [int(x) for x in args.levels.split(",")]:
        r = asyncio.run(level(args.base, image, c, max(args.per_level, c)))
        rows.append(r)
        print(f"{c:>4}{r['requests']:>5}{r['wall_s']:>7}{r['throughput_per_min']:>7}{r['latency_p50_s']:>7}"
              f"{r['latency_p95_s']:>7}{r['latency_max_s']:>7}{r['health_p50_ms']:>10}ms{r['health_max_ms']:>10}ms  {r['statuses']}")
    if args.report:
        args.report.write_text(json.dumps({"image": image_path.name, "levels": rows}, ensure_ascii=False, indent=2),
                               encoding="utf-8")
        print(f"report → {args.report}")


if __name__ == "__main__":
    main()
