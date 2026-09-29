"""Loguru 로깅 설정.

main lifespan 기동 시 setup_logging 을 한 번 호출한다.
기본 핸들러를 제거한 뒤 stderr 와 (선택) backend/logs 파일로 출력한다.
"""

import sys
from pathlib import Path

from loguru import logger

_FORMAT_CONSOLE = (
    "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
    "<level>{level: <8}</level> | "
    "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
    "<level>{message}</level>"
)
_FORMAT_FILE = "{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"


def setup_logging(
    debug: bool = True,
    log_dir: Path | None = None,
    retention_days: int = 14,
) -> None:
    """로그 레벨·포맷을 앱 전역에 적용.

    debug=True  → DEBUG
    debug=False → INFO
    log_dir 가 있으면 app_YYYY-MM-DD.log 로 자정마다 회전, retention_days 뒤 삭제.
    파일은 UTF-8 고정 (Windows 콘솔 cp949 와 무관하게 한글 보존).
    """
    logger.remove()  # 기본 sink 제거 (중복 방지)
    level = "DEBUG" if debug else "INFO"
    logger.add(sys.stderr, level=level, format=_FORMAT_CONSOLE)

    if log_dir is not None:
        log_dir.mkdir(parents=True, exist_ok=True)
        logger.add(
            log_dir / "app_{time:YYYY-MM-DD}.log",
            level=level,
            format=_FORMAT_FILE,
            rotation="00:00",
            retention=f"{retention_days} days",
            encoding="utf-8",
            enqueue=True,  # 멀티스레드 요청에서도 안전하게 기록
        )
