"""
Logging facade.

The project originally uses `loguru`, but some environments running the toolkit
may not have it installed. This module provides a compatible `logger` object
backed by stdlib `logging` as a fallback.
"""

from __future__ import annotations

from pathlib import Path
import logging


try:
    # Prefer loguru when available.
    from loguru import logger as _loguru_logger  # type: ignore

    _loguru_logger.remove()
except Exception:
    _loguru_logger = None


if _loguru_logger is not None:
    # Re-add the standard handlers in a loguru-friendly way.
    import sys

    _loguru_logger.remove()
    _loguru_logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - {message}",
        level="DEBUG",
        colorize=True,
    )

    Path("outputs").mkdir(parents=True, exist_ok=True)
    _loguru_logger.add(
        "outputs/toolkit.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name} - {message}",
        rotation="10 MB",
        retention="7 days",
        level="INFO",
    )

    logger = _loguru_logger
else:
    # Minimal compatible logger interface for environments without loguru.
    _base_logger = logging.getLogger("cad_toolkit")
    _base_logger.setLevel(logging.DEBUG)
    _base_logger.propagate = False

    if not _base_logger.handlers:
        console = logging.StreamHandler()
        console.setLevel(logging.DEBUG)
        console.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
                datefmt="%H:%M:%S",
            )
        )
        _base_logger.addHandler(console)

        Path("outputs").mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler("outputs/toolkit.log")
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _base_logger.addHandler(file_handler)

    class _FallbackLogger:
        def debug(self, msg: str):
            _base_logger.debug(msg)

        def info(self, msg: str):
            _base_logger.info(msg)

        def warning(self, msg: str):
            _base_logger.warning(msg)

        def error(self, msg: str):
            _base_logger.error(msg)

        # loguru has `success`; treat it like info.
        def success(self, msg: str):
            _base_logger.info(msg)

    logger = _FallbackLogger()
