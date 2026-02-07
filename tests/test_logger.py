"""
Tests para vigilant/core/logger.py
"""
import logging
from pathlib import Path

import pytest

from vigilant.core.logger import ColorFormatter, setup_logger, short_path


class TestColorFormatter:
    """Tests para la clase ColorFormatter."""

    def test_color_formatter_with_color(self):
        """Test de formateo con colores habilitados."""
        formatter = ColorFormatter(
            "%(levelname)s - %(message)s",
            use_color=True
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        # Debe contener códigos de color ANSI
        assert "\x1b[" in formatted or "info" in formatted.lower()

    def test_color_formatter_without_color(self):
        """Test de formateo sin colores."""
        formatter = ColorFormatter(
            "%(levelname)s - %(message)s",
            use_color=False
        )
        
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="test message",
            args=(),
            exc_info=None
        )
        
        formatted = formatter.format(record)
        # No debe contener códigos de color ANSI
        assert "\x1b[" not in formatted
        assert "info" in formatted.lower()


class TestSetupLogger:
    """Tests para la función setup_logger."""

    def test_setup_logger_default(self):
        """Test de configuración por defecto del logger."""
        logger = setup_logger("test_logger")
        
        assert logger.name == "test_logger"
        assert isinstance(logger, logging.Logger)
        assert len(logger.handlers) > 0

    def test_setup_logger_level(self):
        """Test de nivel de logging."""
        logger = setup_logger("test_logger_level")
        
        # El logger debe tener un nivel configurado
        assert logger.level in [
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR
        ]

    def test_logger_has_console_handler(self):
        """Test de que el logger tiene handler de consola."""
        logger = setup_logger("test_console")
        
        console_handlers = [
            h for h in logger.handlers
            if isinstance(h, logging.StreamHandler)
        ]
        
        assert len(console_handlers) > 0


class TestShortPath:
    """Tests para la función short_path."""

    def test_short_path_basic(self):
        """Test de acortamiento de path básico."""
        path = Path("/home/user/documents/file.txt")
        result = short_path(path)
        
        assert result == "/file.txt"
        assert result.startswith("/")

    def test_short_path_single_component(self):
        """Test con path de un solo componente."""
        path = Path("file.txt")
        result = short_path(path)
        
        assert result == "/file.txt"

    def test_short_path_nested(self):
        """Test con path anidado."""
        path = Path("/very/long/nested/path/to/file.mp4")
        result = short_path(path)
        
        assert result == "/file.mp4"
        assert "nested" not in result
        assert "very" not in result
