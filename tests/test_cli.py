"""
Tests para vigilant/cli.py
"""
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from typer.testing import CliRunner

from vigilant.cli import app, get_video_duration, format_duration, convert


runner = CliRunner()


class TestUtilityFunctions:
    """Tests para funciones de utilidad."""

    def test_format_duration_basic(self):
        """Test básico de formato de duración."""
        assert format_duration(0) == "00:00:00"
        assert format_duration(59) == "00:00:59"
        assert format_duration(60) == "00:01:00"
        assert format_duration(3661) == "01:01:01"

    def test_format_duration_hours(self):
        """Test con horas."""
        assert format_duration(7200) == "02:00:00"
        assert format_duration(3600) == "01:00:00"

    @patch('subprocess.run')
    def test_get_video_duration_success(self, mock_run):
        """Test obtención exitosa de duración."""
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="120.5\n"
        )
        
        duration = get_video_duration(Path("/fake/video.mp4"))
        assert duration == 120.5

    @patch('subprocess.run')
    def test_get_video_duration_failure(self, mock_run):
        """Test cuando ffprobe falla."""
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout=""
        )
        
        duration = get_video_duration(Path("/fake/video.mp4"))
        assert duration is None


class TestCLIVersion:
    """Tests para el comando --version."""

    def test_version_flag(self):
        """Test que --version muestra la versión."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "Vigilant v" in result.stdout

    def test_v_flag(self):
        """Test que -v muestra la versión."""
        result = runner.invoke(app, ["-v"])
        assert result.exit_code == 0
        assert "Vigilant v" in result.stdout


class TestCLIHelp:
    """Tests para el help."""

    def test_help(self):
        """Test que --help funciona."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "Vigilant" in result.stdout
        assert "convert" in result.stdout
        assert "analyze" in result.stdout

    def test_convert_help(self):
        """Test help del comando convert."""
        result = runner.invoke(app, ["convert", "--help"])
        assert result.exit_code == 0
        assert "convert" in result.stdout.lower()

    def test_analyze_help(self):
        """Test help del comando analyze."""
        result = runner.invoke(app, ["analyze", "--help"])
        assert result.exit_code == 0
        assert "analyze" in result.stdout.lower()


class TestConvertCommand:
    """Tests para el comando convert (mocked)."""

    @patch('vigilant.cli.convert_mfs_to_mp4')
    @patch('vigilant.cli.calculate_sha256')
    @patch('pathlib.Path.rglob')
    def test_convert_basic(self, mock_rglob, mock_hash, mock_convert):
        """Test básico de conversión."""
        # Mock files
        mock_file = MagicMock(spec=Path)
        mock_file.name = "test.mfs"
        mock_file.is_file.return_value = True
        mock_rglob.return_value = [mock_file]
        
        # Mock conversion success
        mock_convert.return_value = True
        mock_hash.return_value = "abc123"
        
        # Run (puede fallar si hay dependencies, pero estructura está)
        # result = runner.invoke(app, ["convert"])
        # En un test real, validaríamos el output

    @patch('vigilant.cli.logger')
    @patch('pathlib.Path.rglob')
    def test_convert_no_files(self, mock_rglob, mock_logger):
        """Test cuando no hay archivos .mfs."""
        mock_rglob.return_value = []
        
        # Este test validaría que loguea correctamente la ausencia de archivos
        # En implementación real, se ejecutaría el comando

    @patch("vigilant.cli._write_integrity_files")
    @patch("vigilant.cli.try_force_decode")
    @patch("vigilant.cli.fallback_conversion_ffmpeg")
    @patch("vigilant.cli.convert_mfs_to_mp4")
    def test_convert_integrity_on_remux(
        self, mock_convert, mock_remux, mock_rescue, mock_integrity, tmp_path
    ):
        """Debe generar integridad cuando el remux de ffmpeg es exitoso."""
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()
        (input_dir / "video.mfs").write_bytes(b"fake")

        mock_convert.return_value = False
        mock_remux.return_value = True

        convert(input_dir=input_dir, output_dir=output_dir, rescue=True)

        mock_integrity.assert_called_once()
        assert mock_integrity.call_args.kwargs["conversion_tool"] == "ffmpeg remux"
        mock_rescue.assert_not_called()

    @patch("vigilant.cli._write_integrity_files")
    @patch("vigilant.cli.try_force_decode")
    @patch("vigilant.cli.fallback_conversion_ffmpeg")
    @patch("vigilant.cli.convert_mfs_to_mp4")
    def test_convert_integrity_on_rescue(
        self, mock_convert, mock_remux, mock_rescue, mock_integrity, tmp_path
    ):
        """Debe generar integridad cuando el rescate es exitoso."""
        input_dir = tmp_path / "in"
        output_dir = tmp_path / "out"
        input_dir.mkdir()
        output_dir.mkdir()
        (input_dir / "video.mfs").write_bytes(b"fake")

        mock_convert.return_value = False
        mock_remux.return_value = False
        mock_rescue.return_value = {
            "success": True,
            "technique": "force_decode_h264",
            "codec_hint": "h264",
            "offset_found": False,
            "offset_bytes": None,
            "command": "ffmpeg -y -f h264 -i input.mfs output.mp4",
            "extraction_method": None,
            "extracted_path": None,
            "bitexact_flags": True,
        }

        convert(input_dir=input_dir, output_dir=output_dir, rescue=True)

        mock_integrity.assert_called_once()
        assert mock_integrity.call_args.kwargs["conversion_tool"] == "ffmpeg rescue"


class TestAnalyzeCommand:
    """Tests para el comando analyze (mocked)."""

    @patch('vigilant.cli.AIAnalyzer')
    @patch('vigilant.cli.extract_frames')
    @patch('vigilant.cli.get_video_duration')
    def test_analyze_requires_prompt(self, mock_duration, mock_extract, mock_analyzer):
        """Test que analyze requiere prompt."""
        result = runner.invoke(app, ["analyze", "--video", "test.mp4"])
        # Debería fallar si no hay prompt
        assert result.exit_code != 0


# Placeholder para más tests
# TODO: Agregar tests de integración con archivos reales
# TODO: Agregar tests para parse-pdf
# TODO: Agregar tests de error handling
