"""이미지 인코딩/디코딩 헬퍼.

파이프라인에서는 원본 보존을 위해 .copy() 를 사용하는 것이 원칙이다.
OpenCV 는 기본적으로 BGR / BGRA 채널 순서를 쓴다.
"""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

import cv2
import numpy as np


def decode_image_bytes(data: bytes) -> np.ndarray:
    """이미지 바이트를 BGR ndarray로 디코딩.

    업로드 원본 바이트 → 전처리/세그 입력.
    디코딩 실패 시 ValueError.
    """
    arr = np.frombuffer(data, dtype=np.uint8)
    image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("이미지 바이트 디코딩 실패.")
    return image


def encode_image(
    image: np.ndarray,
    ext: str = ".png",
    quality: int = 95,
) -> bytes:
    """BGR/BGRA 이미지를 바이트로 인코딩.

    JPEG 는 quality, PNG 는 compression 레벨을 사용.
    """
    params: list[int] = []
    if ext.lower() in {".jpg", ".jpeg"}:
        params = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    elif ext.lower() == ".png":
        params = [int(cv2.IMWRITE_PNG_COMPRESSION), 3]
    ok, buf = cv2.imencode(ext, image, params)
    if not ok:
        raise ValueError(f"이미지 인코딩 실패: {ext}.")
    return buf.tobytes()


def resize_keep_aspect(
    image: np.ndarray,
    max_side: int,
) -> Tuple[np.ndarray, float]:
    """긴 변이 max_side 이하가 되도록 리사이즈. (복사본, scale) 반환.

    이미 작으면 복사본 + scale=1.0 만 반환.
    INTER_AREA 는 축소 시 모아레를 줄이는 데 유리하다.
    """
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
    """디렉터리가 없으면 parents 포함 생성."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_image(path: Path, image: np.ndarray) -> Path:
    """경로에 이미지 저장. 상위 디렉터리 자동 생성.

    확장자는 path.suffix 로 OpenCV 가 결정 (jpg/png 등).
    """
    ensure_dir(path.parent)
    ok = cv2.imwrite(str(path), image)
    if not ok:
        raise ValueError(f"이미지 저장 실패: {path}")
    return path
