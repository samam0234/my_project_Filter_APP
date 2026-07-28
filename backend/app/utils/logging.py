"""Loguru 로깅 설정.

main lifespan 기동 시 setup_logging 을 한 번 호출한다.
기본 핸들러를 제거한 뒤 stderr 로만 출력한다.
"""

import sys

from loguru import logger


def setup_logging(debug: bool = True) -> None:
    """로그 레벨·포맷을 앱 전역에 적용.

    debug=True  → DEBUG
    debug=False → INFO
    """
    logger.remove()  # 기본 sink 제거 (중복 방지)
    level = "DEBUG" if debug else "INFO"
    logger.add(
        sys.stderr,
        level=level,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan> - "
            "<level>{message}</level>"
        ),
    )
