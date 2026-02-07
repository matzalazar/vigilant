"""
Tests para el módulo de seguridad.
"""

import pytest
from pathlib import Path
import tempfile
from vigilant.core.security import (
    validate_path,
    sanitize_prompt,
    validate_file_exists,
    DANGEROUS_CHARS
)


def test_validate_path_safe_path():
    """Path seguro debe validarse correctamente."""
    safe = validate_path("/home/user/video.mp4")
    assert isinstance(safe, Path)
    assert safe.is_absolute()


def test_validate_path_dangerous_semicolon():
    """Path con punto y coma debe fallar."""
    with pytest.raises(ValueError, match="Path inseguro"):
        validate_path("/home/user/video.mp4; rm -rf /")


def test_validate_path_dangerous_pipe():
    """Path con pipe debe fallar."""
    with pytest.raises(ValueError, match="Path inseguro"):
        validate_path("/home/user/video.mp4 | cat")


def test_validate_path_dangerous_ampersand():
    """Path con ampersand debe fallar."""
    with pytest.raises(ValueError, match="Path inseguro"):
        validate_path("/home/user/video.mp4 & malicious")


def test_validate_path_dangerous_dollar():
    """Path con dollar debe fallar."""
    with pytest.raises(ValueError, match="Path inseguro"):
        validate_path("/home/user/$INJECT")


def test_validate_path_dangerous_backtick():
    """Path con backtick debe fallar."""
    with pytest.raises(ValueError, match="Path inseguro"):
        validate_path("/home/user/`whoami`")


def test_validate_path_dangerous_newline():
    """Path con newline debe fallar."""
    with pytest.raises(ValueError, match="Path inseguro"):
        validate_path("/home/user/video.mp4\nmalicious")


def test_sanitize_prompt_clean():
    """Prompt limpio debe pasarse sin cambios."""
    prompt = "buscar persona con chaqueta roja"
    result = sanitize_prompt(prompt)
    assert result == prompt


def test_sanitize_prompt_control_chars():
    """Prompt con caracteres de control debe limpiarse."""
    prompt = "buscar\x00persona\x01con\x02mochila"
    result = sanitize_prompt(prompt)
    assert "\x00" not in result
    assert "\x01" not in result
    assert "\x02" not in result
    assert "buscar" in result
    assert "persona" in result


def test_sanitize_prompt_max_length():
    """Prompt muy largo debe truncarse."""
    long_prompt = "a" * 2000
    result = sanitize_prompt(long_prompt, max_len=100)
    assert len(result) == 100


def test_sanitize_prompt_whitespace_preserved():
    """Espacios y tabs legítimos deben preservarse."""
    prompt = "buscar  persona\tcon   espacios"
    result = sanitize_prompt(prompt)
    assert "  " in result or " " in result
    

def test_validate_file_exists_valid():
    """Archivo existente debe validarse correctamente."""
    with tempfile.NamedTemporaryFile(delete=False) as f:
        test_file = Path(f.name)
        f.write(b"test content")
    
    try:
        validated = validate_file_exists(test_file)
        assert validated == test_file
    finally:
        test_file.unlink()


def test_validate_file_exists_not_found():
    """Archivo inexistente debe lanzar FileNotFoundError."""
    fake_path = Path("/tmp/nonexistent_xyz_file.mp4")
    with pytest.raises(FileNotFoundError, match="no encontrado"):
        validate_file_exists(fake_path)


def test_validate_file_exists_is_directory():
    """Directorio debe lanzar ValueError."""
    with tempfile.TemporaryDirectory() as tmpdir:
        dir_path = Path(tmpdir)
        with pytest.raises(ValueError, match="No es un archivo"):
            validate_file_exists(dir_path)


def test_dangerous_chars_comprehensive():
    """Verificar que todos los caracteres peligrosos están definidos."""
    expected = [';', '|', '&', '$', '`', '\n', '\r', '\0']
    for char in expected:
        assert char in DANGEROUS_CHARS, f"Falta carácter peligroso: {repr(char)}"
