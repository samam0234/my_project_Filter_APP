"""git 에 넣지 않는 큰 모델 파일을 받아 오기 — 체크섬으로 확인한다.

배포 서버에는 `backend/models/` 가 비어 있다. 지금은 대상 지우기용 LaMa(208MB)만 자동으로 받는다
(YOLO · SegFormer 는 학습 · 변환으로 만드는 파일이라 별도 — backend/models/README.md).

- `fetch(name)`: 임시 파일(.part)로 받고 SHA-256 이 맞을 때만 제자리로 옮긴다. 이미 있고 체크섬이 맞으면 건너뛴다
- `start_background(settings)`: 기동 시 — `MODEL_AUTO_DOWNLOAD=true` 이고 LaMa 를 쓸 설정인데 파일이 없으면 백그라운드에서 받는다.
  받는 동안 대상 지우기는 Telea 로 동작하고, 받고 나면 다음 요청부터 LaMa (services/inpaint 가 파일이 생기면 다시 로드)
- 손으로: `python scripts/fetch_models.py` (저장소 루트) 또는 `docker exec cut_and_keep-backend-1 python -m app.services.model_fetch`
"""

from __future__ import annotations

import hashlib
import sys
import threading
import urllib.request
from dataclasses import dataclass
from pathlib import Path

from loguru import logger

from app.core.config import Settings, get_settings


@dataclass(frozen=True)
class ModelFile:
    name: str
    url: str
    sha256: str
    size: int
    license: str


MODELS = {
    "lama": ModelFile(
        name="lama",
        # Carve/LaMa-ONNX (big-lama 의 ONNX 판, 512×512 고정) — docs/vaildates/inpaint-20261009.md
        url="https://huggingface.co/Carve/LaMa-ONNX/resolve/main/lama_fp32.onnx",
        sha256="1faef5301d78db7dda502fe59966957ec4b79dd64e16f03ed96913c7a4eb68d6",
        size=208_044_816,
        license="Apache-2.0",
    ),
}


def target_path(name: str, settings: Settings) -> Path:
    if name == "lama":
        return settings.inpaint_model_file
    raise KeyError(name)


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def fetch(name: str, settings: Settings | None = None, *, timeout: float = 60.0) -> Path:
    """모델 하나를 받아 체크섬을 확인한다. 실패하면 예외 (임시 파일은 지운다)."""
    settings = settings or get_settings()
    spec = MODELS[name]
    dst = target_path(name, settings)
    if dst.is_file() and dst.stat().st_size == spec.size and sha256_of(dst) == spec.sha256:
        logger.info("모델 {} 이미 있음 (체크섬 일치): {}", name, dst)
        return dst
    dst.parent.mkdir(parents=True, exist_ok=True)
    part = dst.with_name(dst.name + ".part")
    logger.info("모델 {} 받는 중 ({:.0f}MB, {}): {}", name, spec.size / 1e6, spec.license, spec.url)
    digest = hashlib.sha256()
    try:
        with urllib.request.urlopen(spec.url, timeout=timeout) as resp, part.open("wb") as out:
            for chunk in iter(lambda: resp.read(1 << 20), b""):
                out.write(chunk)
                digest.update(chunk)
        if digest.hexdigest() != spec.sha256:
            raise ValueError(f"체크섬이 다르다 — 받은 파일을 버린다 ({digest.hexdigest()[:12]}… ≠ {spec.sha256[:12]}…)")
        part.replace(dst)
    finally:
        part.unlink(missing_ok=True)
    logger.info("모델 {} 받기 완료: {}", name, dst)
    return dst


def needs_lama(settings: Settings) -> bool:
    return settings.inpaint_engine != "telea" and not settings.inpaint_model_file.is_file()


def start_background(settings: Settings | None = None) -> bool:
    """기동 시 없는 모델을 백그라운드로 받는다. 받기 시작하면 True."""
    settings = settings or get_settings()
    if not settings.model_auto_download or not needs_lama(settings):
        return False

    def run() -> None:
        try:
            fetch("lama", settings)
        except Exception:
            logger.exception("LaMa 모델 자동 받기 실패 — 대상 지우기는 Telea 로 동작 (python scripts/fetch_models.py 로 다시 시도)")

    threading.Thread(target=run, name="model-fetch", daemon=True).start()
    return True


def main(argv: list[str]) -> int:
    names = argv[1:] or list(MODELS)
    for name in names:
        try:
            print(f"{name}: {fetch(name)}")
        except Exception as exc:  # 명령줄에서는 원인을 보여 주고 다음 모델로
            print(f"{name}: 실패 — {exc}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
