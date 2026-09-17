"""Logger dùng chung — gọi get_logger(__name__) ở bất kỳ module nào cần log.

Mức log đọc qua config.get_log_level() (biến môi trường LOG_LEVEL, mặc định
INFO) — không hardcode.
"""

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
