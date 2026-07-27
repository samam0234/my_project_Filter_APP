"""Image encode/decode helpers. Always preserve originals via .copy() in pipelines."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


def decode_image_bytes(data: bytes) -> np.ndarray:
    """Decode image bytes to BGR ndarray."""
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("Failed to decode image bytes.")
    return image


def encode_image(
    image: np.ndarray,
    ext: str = ".png",
    quality: int = 95,
) -> bytes:
    """Encode BGR or BGRA image to bytes."""
    params: list[int] = []
    if ext.lower() in {".jpg", ".jpeg"}:
        params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    elif ext.lower() == ".png":
        params = [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
    ok, buf = cv2.imencode(ext, image, params)
    if not ok:
        raise ValueError(f"Failed to encode image as {ext}.")
    return buf.tobytes()


def resize_keep_aspect(
    image: np.ndarray,
    max_side: int,
) -> Tuple[np.ndarray, float]:
    """Resize so longest side <= max_side. Returns (image_copy, scale)."""
    src = image.copy()
    h, w = src.shape[:2]
    longest = max(h, w)
    if longest <= max_side:
        return src, 1.0
    scale = max_side / float(longest)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = cv2.resize(src, (new_w, new_h), interpolation=cv2.INTER_AREA)
    return resized, scale


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_image(path: Path, image: np.ndarray) -> Path:
    ensure_dir(path.parent)
    ok = cv2.imwrite(str(path), image)
    if not ok:
        raise ValueError(f"Failed to write image: {path}")
    return path
