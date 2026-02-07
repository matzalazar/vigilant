"""
Tests para vigilant/intelligence/frame_extractor.py
"""
import subprocess
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from vigilant.intelligence.frame_extractor import (
    _get_time_base,
    _build_filter,
    _run_ffmpeg,
    extract_frames,
)


class TestGetTimeBase:
    """Tests para la función _get_time_base."""

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_get_time_base_success(self, mock_run, mock_video_file):
        """Test de extracción exitosa de time_base."""
        mock_run.return_value = MagicMock(
            stdout="1/30\n",
            returncode=0
        )
        
        result = _get_time_base(mock_video_file)
        
        assert result is not None
        assert isinstance(result, float)
        assert result == pytest.approx(1/30, rel=1e-6)

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_get_time_base_invalid_format(self, mock_run, mock_video_file):
        """Test con formato inválido de time_base."""
        mock_run.return_value = MagicMock(
            stdout="invalid\n",
            returncode=0
        )
        
        result = _get_time_base(mock_video_file)
        
        assert result is None

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_get_time_base_zero_denominator(self, mock_run, mock_video_file):
        """Test con denominador cero."""
        mock_run.return_value = MagicMock(
            stdout="1/0\n",
            returncode=0
        )
        
        result = _get_time_base(mock_video_file)
        
        assert result is None

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_get_time_base_exception(self, mock_run, mock_video_file):
        """Test cuando ffprobe falla."""
        mock_run.side_effect = Exception("ffprobe error")
        
        result = _get_time_base(mock_video_file)
        
        assert result is None


class TestBuildFilter:
    """Tests para la función _build_filter."""

    def test_build_filter_single(self):
        """Test con un solo filtro."""
        result = _build_filter(["scale=640:-1"])
        assert result == "scale=640:-1"

    def test_build_filter_multiple(self):
        """Test con múltiples filtros."""
        result = _build_filter(["fps=1/5", "scale=640:-1", "format=yuvj420p"])
        assert result == "fps=1/5,scale=640:-1,format=yuvj420p"

    def test_build_filter_empty_strings(self):
        """Test ignorando strings vacíos."""
        result = _build_filter(["fps=1/5", "", "scale=640:-1"])
        assert result == "fps=1/5,scale=640:-1"

    def test_build_filter_all_empty(self):
        """Test con todos los filtros vacíos."""
        result = _build_filter(["", "", ""])
        assert result == ""


class TestRunFfmpeg:
    """Tests para la función _run_ffmpeg."""

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_run_ffmpeg_success(self, mock_run, mock_video_file, temp_dir):
        """Test de ejecución exitosa de ffmpeg."""
        mock_run.return_value = MagicMock(returncode=0)
        
        output_pattern = temp_dir / "frame_%d.jpg"
        result = _run_ffmpeg(mock_video_file, "fps=1/5", output_pattern)
        
        assert result is True
        mock_run.assert_called_once()

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_run_ffmpeg_failure(self, mock_run, mock_video_file, temp_dir):
        """Test cuando ffmpeg falla."""
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
        
        output_pattern = temp_dir / "frame_%d.jpg"
        result = _run_ffmpeg(mock_video_file, "fps=1/5", output_pattern)
        
        assert result is False

    @patch("vigilant.intelligence.frame_extractor.subprocess.run")
    def test_run_ffmpeg_empty_filter(self, mock_run, mock_video_file, temp_dir):
        """Test con filtro vacío."""
        mock_run.return_value = MagicMock(returncode=0)
        
        output_pattern = temp_dir / "frame_%d.jpg"
        result = _run_ffmpeg(mock_video_file, "", output_pattern)
        
        assert result is True
        # Verificar que no se pasó el argumento -vf cuando el filtro está vacío
        call_args = mock_run.call_args[0][0]
        if "-vf" in call_args:
            # Si se pasó -vf, el siguiente argumento debe ser vacío
            vf_index = call_args.index("-vf")
            assert call_args[vf_index + 1] == ""


class TestExtractFrames:
    """Tests para la función extract_frames."""

    def test_extract_frames_file_not_found(self, temp_dir):
        """Test cuando el archivo de video no existe."""
        fake_video = temp_dir / "nonexistent.mp4"
        output_dir = temp_dir / "frames"
        
        frames, time_base = extract_frames(fake_video, output_dir)
        
        assert frames == []
        assert time_base is None

    @patch("vigilant.intelligence.frame_extractor._get_time_base")
    @patch("vigilant.intelligence.frame_extractor._run_ffmpeg")
    def test_extract_frames_interval_mode(
        self, mock_run_ffmpeg, mock_get_time_base, mock_video_file, temp_dir
    ):
        """Test de extracción en modo intervalo."""
        mock_get_time_base.return_value = 1/30
        mock_run_ffmpeg.return_value = True
        
        # Crear archivos de frames simulados
        output_dir = temp_dir / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{mock_video_file.stem}_1.jpg").touch()
        (output_dir / f"{mock_video_file.stem}_2.jpg").touch()
        
        frames, time_base = extract_frames(
            mock_video_file,
            output_dir,
            interval_seconds=5,
            mode="interval"
        )
        
        assert len(frames) == 2
        assert time_base == pytest.approx(1/30, rel=1e-6)
        mock_run_ffmpeg.assert_called_once()

    @patch("vigilant.intelligence.frame_extractor._get_time_base")
    @patch("vigilant.intelligence.frame_extractor._run_ffmpeg")
    def test_extract_frames_scene_mode(
        self, mock_run_ffmpeg, mock_get_time_base, mock_video_file, temp_dir
    ):
        """Test de extracción en modo escena."""
        mock_get_time_base.return_value = 1/30
        mock_run_ffmpeg.return_value = True
        
        output_dir = temp_dir / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / f"{mock_video_file.stem}_1.jpg").touch()
        
        frames, time_base = extract_frames(
            mock_video_file,
            output_dir,
            mode="scene",
            scene_threshold=0.20
        )
        
        assert len(frames) >= 1
        assert time_base == pytest.approx(1/30, rel=1e-6)

    @patch("vigilant.intelligence.frame_extractor._get_time_base")
    @patch("vigilant.intelligence.frame_extractor._run_ffmpeg")
    def test_extract_frames_combined_mode(
        self, mock_run_ffmpeg, mock_get_time_base, mock_video_file, temp_dir
    ):
        """Test de extracción en modo combinado interval+scene."""
        mock_get_time_base.return_value = 1/30
        mock_run_ffmpeg.return_value = True
        
        output_dir = temp_dir / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        # Simular frames de intervalo y escena
        (output_dir / f"{mock_video_file.stem}_i_1.jpg").touch()
        (output_dir / f"{mock_video_file.stem}_s_2.jpg").touch()
        
        frames, time_base = extract_frames(
            mock_video_file,
            output_dir,
            mode="interval+scene",
            interval_seconds=5,
            scene_threshold=0.20
        )
        
        assert len(frames) >= 1
        assert time_base == pytest.approx(1/30, rel=1e-6)
        # En modo combinado se llama a ffmpeg dos veces
        assert mock_run_ffmpeg.call_count == 2

    @patch("vigilant.intelligence.frame_extractor._get_time_base")
    @patch("vigilant.intelligence.frame_extractor._run_ffmpeg")
    def test_extract_frames_invalid_mode(
        self, mock_run_ffmpeg, mock_get_time_base, mock_video_file, temp_dir
    ):
        """Test con modo inválido (debe usar 'interval' por defecto)."""
        mock_get_time_base.return_value = 1/30
        mock_run_ffmpeg.return_value = True
        
        output_dir = temp_dir / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frames, time_base = extract_frames(
            mock_video_file,
            output_dir,
            mode="invalid_mode"
        )
        
        # Debe caer al modo interval por defecto
        mock_run_ffmpeg.assert_called_once()

    @patch("vigilant.intelligence.frame_extractor._get_time_base")
    @patch("vigilant.intelligence.frame_extractor._run_ffmpeg")
    def test_extract_frames_with_scale(
        self, mock_run_ffmpeg, mock_get_time_base, mock_video_file, temp_dir
    ):
        """Test de extracción con escalado."""
        mock_get_time_base.return_value = 1/30
        mock_run_ffmpeg.return_value = True
        
        output_dir = temp_dir / "frames"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        frames, time_base = extract_frames(
            mock_video_file,
            output_dir,
            mode="interval",
            scale_width=640
        )
        
        # Verificar que se pasó el filtro de escala
        call_args = mock_run_ffmpeg.call_args[0][1]
        assert "scale=640:-1" in call_args
