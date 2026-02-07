"""
Fixtures compartidas de pytest para la suite de tests de Vigilant.
"""
import os

os.environ.setdefault("VIGILANT_CLI", "1")
import tempfile
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Crea un directorio temporal para tests.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_yaml_config(temp_dir: Path) -> Path:
    """
    Crea un archivo de configuración YAML de ejemplo para tests.
    """
    config_file = temp_dir / "test_config.yaml"
    config_content = """
logging:
  level: "INFO"

handbrake:
  preset: "Fast 1080p30"

ai:
  ollama_url: "http://localhost:11434"
  model: "llava:13b"
  filter_backend: "llava"
  filter_model: "llava:13b"
  sample_interval: 1
  filter_min_confidence: 0.60

frames:
  mode: "interval"
  scene_threshold: 0.20
  scale: 640

yolo:
  model: "/path/to/yolov8n.pt"
  confidence: 0.25
  device: "cpu"

raw:
  pix_fmt: "yuv420p"
  resolution: "1280x720"
  framerate: 30
"""
    config_file.write_text(config_content)
    return config_file


@pytest.fixture
def sample_pdf_text() -> str:
    """
    Contenido de PDF de ejemplo para testing del parser.
    """
    return """
Usuario: admin
Fecha de inicio: 2024-01-15 10:00:00
Fecha de finalización: 2024-01-15 10:05:00
Tipo: Exportación
Dividir archivo: No
Firmar: Sí
Marca de agua: No

Nombre del canal: Cámara 1
Fecha de inicio: 2024-01-15 10:00:00
Fecha de finalización: 2024-01-15 10:02:00
Estado: Completo
- /output/camara1_2024-01-15.mp4

Nombre del canal: Cámara 2
Fecha de inicio: 2024-01-15 10:02:00
Fecha de finalización: 2024-01-15 10:05:00
Estado: Completo
- /output/camara2_2024-01-15.mp4
"""


@pytest.fixture
def mock_video_file(temp_dir: Path) -> Path:
    """
    Crea un archivo de video vacío para tests.
    """
    video_file = temp_dir / "test_video.mp4"
    video_file.write_bytes(b"fake video content")
    return video_file


@pytest.fixture
def mock_mfs_file(temp_dir: Path) -> Path:
    """
    Crea un archivo .mfs vacío para tests.
    """
    mfs_file = temp_dir / "test_video.mfs"
    mfs_file.write_bytes(b"fake mfs content")
    return mfs_file
