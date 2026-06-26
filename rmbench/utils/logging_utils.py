"""Logging utilities for RMBench."""
from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    rich_handler: bool = True,
) -> None:
    """Configure root logger with optional file and rich console output.

    Args:
        level: Logging level string ("DEBUG", "INFO", "WARNING", "ERROR").
        log_file: Optional path to write logs to file.
        rich_handler: Use rich logging handler for colored console output.
    """
    handlers: list[logging.Handler] = []

    if rich_handler:
        try:
            from rich.logging import RichHandler
            handlers.append(RichHandler(
                rich_tracebacks=True,
                show_path=False,
                markup=True,
            ))
        except ImportError:
            handlers.append(logging.StreamHandler(sys.stdout))
    else:
        handlers.append(logging.StreamHandler(sys.stdout))

    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(path, encoding="utf-8")
        file_handler.setFormatter(logging.Formatter(
            "%(asctime)s — %(name)s — %(levelname)s — %(message)s"
        ))
        handlers.append(file_handler)

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        handlers=handlers,
        force=True,
    )

    # Silence noisy third-party loggers
    for noisy in ["httpx", "httpcore", "urllib3", "faiss"]:
        logging.getLogger(noisy).setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Get a named logger.

    Args:
        name: Logger name (usually __name__ of the calling module).

    Returns:
        Configured Logger instance.
    """
    return logging.getLogger(name)
