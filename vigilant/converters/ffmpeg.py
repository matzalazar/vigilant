from vigilant.core.runtime import require_cli
require_cli()

import subprocess
from pathlib import Path
from vigilant.core.logger import logger, short_path
from vigilant.core.security import validate_path

_BITEXACT_FLAGS = [
    "-map_metadata", "-1",
    "-map_chapters", "-1",
    "-fflags", "+bitexact",
    "-flags:v", "+bitexact",
    "-flags:a", "+bitexact",
]

def normalize_container_metadata(input_path: Path, output_path: Path) -> bool:
    """
    Remux para normalizar metadata del contenedor y mejorar reproducibilidad.
    """
    if not input_path.exists():
        logger.error(f"archivo no encontrado path={short_path(input_path)}")
        return False

    try:
        safe_input = validate_path(input_path)
        safe_output = validate_path(output_path)
    except ValueError as e:
        logger.error(f"path invalido err={e}")
        return False

    command = [
        "ffmpeg", "-y", "-i", str(safe_input),
        *_BITEXACT_FLAGS,
        "-c", "copy", str(safe_output),
    ]
    try:
        logger.info(f"normalizando path={short_path(input_path)}")
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"normalizado ok path={short_path(output_path)}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        logger.error(f"normalizado fallo path={short_path(input_path)}")
        return False

def fallback_conversion_ffmpeg(input_path: Path, output_path: Path) -> bool:
    """
    Intenta convertir/remuxear usando ffmpeg básico (copy).
    
    Args:
        input_path: Ruta al archivo de entrada
        output_path: Ruta al archivo de salida
        
    Returns:
        bool: True si el remux fue exitoso, False en caso contrario
    """
    if not input_path.exists():
        logger.error(f"archivo no encontrado path={short_path(input_path)}")
        return False

    try:
        safe_input = validate_path(input_path)
        safe_output = validate_path(output_path)
    except ValueError as e:
        logger.error(f"path invalido err={e}")
        return False

    command = [
        "ffmpeg", "-y", "-i", str(safe_input),
        *_BITEXACT_FLAGS,
        "-c", "copy", str(safe_output),
    ]

    try:
        logger.info(f"remux path={short_path(input_path)}")
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        logger.info(f"remux ok path={short_path(input_path)}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError, OSError):
        logger.error(f"remux fallo path={short_path(input_path)}")
        return False
