"""
Tests para vigilant/converters/handbrake.py
"""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from vigilant.converters.handbrake import convert_mfs_to_mp4, _one_line


class TestOneLine:
    """Tests para la función _one_line."""

    def test_one_line_basic(self):
        """Test de formateo básico de texto."""
        text = "line1\nline2\nline3"
        result = _one_line(text)
        assert result == "line1 line2 line3"

    def test_one_line_whitespace(self):
        """Test con espacios múltiples."""
        text = "word1  word2\t\tword3"
        result = _one_line(text)
        assert result == "word1 word2 word3"

    def test_one_line_empty(self):
        """Test con string vacío."""
        result = _one_line("")
        assert result == ""


class TestConvertMfsToMp4:
    """Tests para la función convert_mfs_to_mp4."""

    @patch("vigilant.converters.handbrake.subprocess.run")
    @patch("vigilant.converters.handbrake.os.path.isfile")
    def test_convert_success(self, mock_isfile, mock_run, mock_mfs_file, temp_dir):
        """Test de conversión exitosa."""
        mock_isfile.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        output_path = temp_dir / "output.mp4"
        result = convert_mfs_to_mp4(mock_mfs_file, output_path)
        
        assert result is True
        mock_run.assert_called_once()
        
        # Verificar que se llamó con los argumentos correctos
        call_args = mock_run.call_args[0][0]
        assert "HandBrakeCLI" in call_args
        assert "-i" in call_args
        assert "-o" in call_args

    @patch("vigilant.converters.handbrake.os.path.isfile")
    def test_convert_file_not_found(self, mock_isfile):
        """Test cuando el archivo de entrada no existe."""
        mock_isfile.return_value = False
        
        result = convert_mfs_to_mp4("/fake/path.mfs", "/fake/output.mp4")
        
        assert result is False

    @patch("vigilant.converters.handbrake.subprocess.run")
    @patch("vigilant.converters.handbrake.os.path.isfile")
    def test_convert_handbrake_failure(self, mock_isfile, mock_run, mock_mfs_file, temp_dir):
        """Test cuando HandBrake falla."""
        mock_isfile.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "HandBrakeCLI", stderr=b"Error message"
        )
        
        output_path = temp_dir / "output.mp4"
        result = convert_mfs_to_mp4(mock_mfs_file, output_path)
        
        assert result is False

    @patch("vigilant.converters.handbrake.subprocess.run")
    @patch("vigilant.converters.handbrake.os.path.isfile")
    def test_convert_custom_preset(self, mock_isfile, mock_run, mock_mfs_file, temp_dir):
        """Test con preset personalizado."""
        mock_isfile.return_value = True
        mock_run.return_value = MagicMock(returncode=0)
        
        output_path = temp_dir / "output.mp4"
        custom_preset = "Custom Preset"
        result = convert_mfs_to_mp4(mock_mfs_file, output_path, preset=custom_preset)
        
        assert result is True
        
        # Verificar que se usó el preset personalizado
        call_args = mock_run.call_args[0][0]
        assert any(custom_preset in arg for arg in call_args)

    @patch("vigilant.converters.handbrake.subprocess.run")
    @patch("vigilant.converters.handbrake.os.path.isfile")
    def test_convert_stderr_handling(self, mock_isfile, mock_run, mock_mfs_file, temp_dir):
        """Test de manejo de stderr cuando falla."""
        mock_isfile.return_value = True
        error_msg = b"HandBrake error: encoding failed"
        mock_run.side_effect = subprocess.CalledProcessError(
            1, "HandBrakeCLI", stderr=error_msg
        )
        
        output_path = temp_dir / "output.mp4"
        result = convert_mfs_to_mp4(mock_mfs_file, output_path)
        
        assert result is False
