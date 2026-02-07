from vigilant.core.runtime import require_cli
require_cli()

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Union
from .config import config

LEVEL_COLORS = {
    "DEBUG": "\x1b[36m",
    "INFO": "\x1b[32m",
    "WARNING": "\x1b[33m",
    "ERROR": "\x1b[31m",
    "CRITICAL": "\x1b[41m",
}
RESET = "\x1b[0m"


class ColorFormatter(logging.Formatter):
    """Formatter personalizado que agrega colores ANSI a los niveles de log."""
    def __init__(self, *args, use_color: bool = False, **kwargs):
        super().__init__(*args, **kwargs)
        self.use_color = use_color

    def format(self, record: logging.LogRecord) -> str:
        original_levelname = record.levelname
        label = original_levelname.lower()
        if self.use_color and original_levelname in LEVEL_COLORS:
            label = f"{LEVEL_COLORS[original_levelname]}{label}{RESET}"
        record.levelname = label
        try:
            return super().format(record)
        finally:
            record.levelname = original_levelname


def setup_logger(name: str = "vigilant") -> logging.Logger:
    """
    Configura el logger con handlers de consola y archivo.
    
    Args:
        name: Nombre del logger
        
    Returns:
        logging.Logger: Logger configurado
    """
    logger = logging.getLogger(name)

    level_name = getattr(config, "LOG_LEVEL", os.getenv("VIGILANT_LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    if not logger.handlers:
        use_color = sys.stdout.isatty() and os.getenv("NO_COLOR") is None

        # Handler de consola (formato minimal)
        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(level)
        console_fmt = ColorFormatter(
            "%(asctime)s [%(levelname)s] %(message)s",
            datefmt="%H:%M:%S",
            use_color=use_color,
        )
        ch.setFormatter(console_fmt)
        logger.addHandler(ch)

        # Handler de archivo (rotativo, verboso)
        config.LOGS_DIR.mkdir(parents=True, exist_ok=True)
        fh = RotatingFileHandler(
            config.LOGS_DIR / "vigilant.log",
            maxBytes=5 * 1024 * 1024,
            backupCount=5,
            encoding="utf-8",
        )
        fh.setLevel(logging.DEBUG)
        file_fmt = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        fh.setFormatter(file_fmt)
        logger.addHandler(fh)

    return logger


logger = setup_logger()

def short_path(path: Union[Path, str]) -> str:
    """Acorta un path mostrando solo el nombre del archivo."""
    return f"/{Path(path).name}"
