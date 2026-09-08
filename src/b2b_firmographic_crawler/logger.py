from __future__ import annotations

import logging
import os

_DEFAULT_FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"


def get_logger(name: str) -> logging.Logger:
    """Return a consistently configured logger for crawler modules."""
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(os.getenv("CRAWLER_LOG_FORMAT", _DEFAULT_FORMAT))
        )
        logger.addHandler(handler)
        logger.propagate = False

    level_name = os.getenv("CRAWLER_LOG_LEVEL", "INFO").upper()
    logger.setLevel(getattr(logging, level_name, logging.INFO))
    return logger
