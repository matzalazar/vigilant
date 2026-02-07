"""
Tests para vigilant/converters/rescue.py
"""
import pytest
import subprocess
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock
import tempfile

from vigilant.converters.rescue import (
    _read_header,
    detect_codec_hint,
    find_start_code_offset,
    try_force_decode
)


class TestHeaderReading:
    """Tests para lectura de headers."""

    def test_read_header_success(self):
        """Test lectura exitosa de header."""
        fake_data = b"test" * 128  # 512 bytes
        
        with patch("builtins.open", mock_open(read_data=fake_data)):
            header = _read_header(Path("/fake/file.mfs"))
            assert len(header) == 512
            assert header == fake_data

    def test_read_header_small_file(self):
        """Test con archivo más pequeño que 512 bytes."""
        fake_data = b"small"
        
        with patch("builtins.open", mock_open(read_data=fake_data)):
            header = _read_header(Path("/fake/file.mfs"))
            assert header == fake_data

    def test_read_header_file_not_found(self):
        """Test con archivo inexistente."""
        with patch("builtins.open", side_effect=FileNotFoundError):
            header = _read_header(Path("/nonexistent.mfs"))
            assert header == b""


class TestCodecDetection:
    """Tests para detección de codec."""

    def test_detect_hevc_hvc1(self, tmp_path):
        """Test detección de HEVC con firma hvc1."""
        header = b"some data " + b"hvc1" + b" more data"
        path = tmp_path / "video.mfs"
        path.write_bytes(header)
        assert detect_codec_hint(path) == "hevc"

    def test_detect_hevc_hev1(self, tmp_path):
        """Test detección de HEVC con firma hev1."""
        header = b"prefix " + b"hev1" + b" suffix"
        path = tmp_path / "video.mfs"
        path.write_bytes(header)
        assert detect_codec_hint(path) == "hevc"

    def test_detect_hevc_direct(self, tmp_path):
        """Test detección de HEVC directo."""
        header = b"data " + b"hevc" + b" data"
        path = tmp_path / "video.mfs"
        path.write_bytes(header)
        assert detect_codec_hint(path) == "hevc"

    def test_detect_h264_avc1(self, tmp_path):
        """Test detección de H.264 con firma avc1."""
        header = b"start " + b"avc1" + b" end"
        path = tmp_path / "video.mfs"
        path.write_bytes(header)
        assert detect_codec_hint(path) == "h264"

    def test_detect_h264_direct(self, tmp_path):
        """Test detección de H.264 directo."""
        header = b"prefix " + b"h264" + b" suffix"
        path = tmp_path / "video.mfs"
        path.write_bytes(header)
        assert detect_codec_hint(path) == "h264"

    def test_no_codec_detected(self, tmp_path):
        """Test cuando no se detecta codec."""
        header = b"random data without codec signatures"
        path = tmp_path / "video.mfs"
        path.write_bytes(header)
        assert detect_codec_hint(path) is None


class TestStartCodeDetection:
    """Tests para detección de NAL start codes."""

    def test_find_4_byte_start_code(self, tmp_path):
        """Test detección de start code de 4 bytes."""
        # NAL start code: 0x00 0x00 0x00 0x01
        data = b"garbage" + b"\x00\x00\x00\x01" + b"more data"
        path = tmp_path / "video.mfs"
        path.write_bytes(data)
        offset = find_start_code_offset(path)
        assert offset == 7  # Position donde empieza el start code

    def test_find_3_byte_start_code(self, tmp_path):
        """Test detección de start code de 3 bytes."""
        # NAL start code: 0x00 0x00 0x01
        data = b"prefix" + b"\x00\x00\x01" + b"suffix"
        path = tmp_path / "video.mfs"
        path.write_bytes(data)
        offset = find_start_code_offset(path)
        assert offset == 6

    def test_no_start_code_found(self, tmp_path):
        """Test cuando no hay start code."""
        data = b"no start codes here just random bytes"
        path = tmp_path / "video.mfs"
        path.write_bytes(data)
        offset = find_start_code_offset(path)
        assert offset is None

    def test_start_code_at_beginning(self, tmp_path):
        """Test start code al inicio del archivo."""
        data = b"\x00\x00\x00\x01video data"
        path = tmp_path / "video.mfs"
        path.write_bytes(data)
        offset = find_start_code_offset(path)
        assert offset == 0


class TestForceDecodeIntegration:
    """Tests de integración para try_force_decode."""

    @patch('vigilant.converters.rescue.subprocess.run')
    @patch('vigilant.converters.rescue._read_header')
    @patch('vigilant.converters.rescue.detect_codec_hint')
    def test_force_decode_with_codec_hint(self, mock_detect, mock_header, mock_run):
        """Test force decode cuando se detecta codec."""
        mock_header.return_value = b"fake header"
        mock_detect.return_value = "hevc"
        mock_run.return_value = MagicMock(returncode=0)

        source = Path("/fake/input.mfs")
        output = Path("/fake/output.mp4")
        
        result = try_force_decode(source, output)
        
        # Debería intentar con HEVC primero
        # En implementación real, verificaríamos los argumentos de subprocess
        assert mock_run.called
        assert result["success"] is True

    @patch('vigilant.converters.rescue.subprocess.run')
    @patch('vigilant.converters.rescue._read_header')
    @patch('vigilant.converters.rescue.detect_codec_hint')
    def test_force_decode_no_codec_hint(self, mock_detect, mock_header, mock_run):
        """Test force decode sin codec hint detectado."""
        mock_header.return_value = b"unknown"
        mock_detect.return_value = None
        mock_run.return_value = MagicMock(returncode=0)

        source = Path("/fake/input.mfs")
        output = Path("/fake/output.mp4")
        
        result = try_force_decode(source, output)
        
        # Debería intentar con codecs por defecto
        assert mock_run.called
        assert result["success"] is True

    @patch('vigilant.converters.rescue.subprocess.run')
    def test_force_decode_all_fail(self, mock_run):
        """Test cuando todos los intentos fallan."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")

        source = Path("/fake/input.mfs")
        output = Path("/fake/output.mp4")
        
        result = try_force_decode(source, output)

        assert result["success"] is False


# Placeholder para más tests
# TODO: Test de extracción desde offset
# TODO: Test de rawvideo fallback
# TODO: Test de limpieza de archivos temporales
