"""Logger dùng chung cho toàn bộ ứng dụng."""

from __future__ import annotations

import logging

from src.utils.config import get_log_level


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(get_log_level())
    return logger
