#!/usr/bin/env python3
"""배포 서버로 옮길 모델 파일 묶기 · 확인 — 모델은 git 에 없다 (backend/models/, 수백 MB).

  pack     지금 .env 설정이 실제로 쓰는 모델만 골라 tar 로 묶고, 파일마다 SHA-256 목록(models.sha256.json)을 만든다
           --gpu: GPU 서버용 — LoRA 어댑터 + 베이스 모델(training/models/qwen2.5-1.5b-instruct, 약 3GB)도
           YOLO_MODEL_PATH · STUFF_MODEL_PATH · INPAINT_MODEL_PATH (+ LLM_PROVIDER/LLM_FALLBACK 이 lora 면 LoRA 어댑터 폴더)
           실험용 · 백업(lora_prev_* · 다른 크기 YOLO)은 넣지 않는다
  verify   서버에서 풀어 놓은 파일을 목록과 대조 (scripts/deploy_check.py server --models-manifest 도 같은 일을 한다)

LaMa 는 서버가 받을 수도 있다 (MODEL_AUTO_DOWNLOAD · scripts/fetch_models.py, 체크섬 확인).
실행: python scripts/models_bundle.py pack --out dist/models.tar
      (서버) tar -xf models.tar && python scripts/models_bundle.py verify models.sha256.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import tarfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"


def _env() -> dict[str, str]:
    out = {}
    p = ROOT / ".env"
    if p.is_file():
        for line in p.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip().strip('"').strip("'")
    return out


GPU_BASE = ROOT / "training" / "models" / "qwen2.5-1.5b-instruct"  # docker-compose.gpu.yml 의 LORA_BASE_DIR 기본값


def wanted_files(env: dict[str, str], gpu: bool = False) -> list[Path]:
    """설정이 쓰는 모델 파일 (저장소 루트 기준 상대 경로가 되도록 backend/ 안의 절대 경로)."""
    rels = [
        env.get("YOLO_MODEL_PATH", "models/yolo26m-seg.pt"),
        env.get("STUFF_MODEL_PATH", "models/segformer-ade.onnx"),
        env.get("INPAINT_MODEL_PATH", "models/lama_fp32.onnx"),
    ]
    files = []
    for rel in rels:
        p = BACKEND / rel
        files.append(p)
        if rel.endswith("segformer-ade.onnx"):
            files.append(p.with_name("segformer-ade.labels.json"))  # 클래스 이름 (함께 있어야 한다)
    if gpu or "lora" in (env.get("LLM_PROVIDER", ""), env.get("LLM_FALLBACK", "")):
        adapter = BACKEND / env.get("LORA_ADAPTER_PATH", "models/lora")
        files += sorted(p for p in adapter.glob("*") if p.is_file())
    if gpu:
        # GPU 오버레이는 compose 가 LLM_PROVIDER=lora 를 켜고 베이스 모델 폴더를 붙인다 — 같이 옮겨야 한다 (약 3GB)
        base = Path(env.get("LORA_BASE_DIR") or GPU_BASE)
        base = base if base.is_absolute() else ROOT / base
        files += sorted(p for p in base.glob("*") if p.is_file())
    return files


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pack(args) -> int:
    env = _env()
    files = wanted_files(env, args.gpu)
    missing = [p for p in files if not p.is_file()]
    for p in missing:
        print(f"  ✗ 없음: {p.relative_to(ROOT)}")
    if missing and not args.allow_missing:
        print("없는 파일이 있습니다 (LaMa 는 서버에서 받게 하려면 --allow-missing)")
        return 1
    files = [p for p in files if p.is_file()]
    manifest = {"created": datetime.now().isoformat(timespec="seconds"),
                "files": {p.relative_to(ROOT).as_posix(): sha256(p) for p in files}}
    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    man = out.with_name("models.sha256.json")
    man.write_text(json.dumps(manifest, indent=1), encoding="utf-8")
    with tarfile.open(out, "w") as tar:
        for p in files:
            tar.add(p, arcname=p.relative_to(ROOT).as_posix())
        tar.add(man, arcname="models.sha256.json")
    total = sum(p.stat().st_size for p in files) / 1e6
    for p in files:
        print(f"  + {p.relative_to(ROOT).as_posix()} ({p.stat().st_size / 1e6:.1f}MB)")
    print(f"{len(files)}개 {total:.0f}MB → {out} (+ {man.name})")
    return 0


def verify(args) -> int:
    manifest = json.loads(Path(args.manifest).read_text(encoding="utf-8"))
    bad = 0
    for rel, digest in manifest["files"].items():
        p = ROOT / rel
        if not p.is_file():
            print(f"  ✗ 없음 {rel}")
            bad += 1
        elif sha256(p) != digest:
            print(f"  ✗ 체크섬 불일치 {rel}")
            bad += 1
        else:
            print(f"  ✓ {rel}")
    print("문제 없음" if not bad else f"문제 {bad}건")
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="모델 파일 묶기 · 확인")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pack")
    p.add_argument("--out", type=Path, default=ROOT / "dist" / "models.tar")
    p.add_argument("--allow-missing", action="store_true")
    p.add_argument("--gpu", action="store_true", help="GPU 서버(docker-compose.gpu.yml)용 — LoRA 어댑터 + 베이스 모델(약 3GB)도 묶는다")
    v = sub.add_parser("verify")
    v.add_argument("manifest")
    args = ap.parse_args()
    return pack(args) if args.cmd == "pack" else verify(args)


if __name__ == "__main__":
    sys.exit(main())
