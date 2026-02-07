from vigilant.core.runtime import require_cli
require_cli()

import os
import re
import subprocess
from typing import List
from vigilant.core.config import config
from vigilant.core.logger import logger, short_path
from vigilant.core.security import validate_path

def _one_line(text: str, max_len: int = 600) -> str:
    # Keep logs single-line and bounded in size to avoid dumping full tool output.
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + "..."
    return cleaned

def build_handbrake_command(input_path, output_path, preset: str) -> List[str]:
    """
    Construye comando HandBrake con paths validados.
    
    Args:
        input_path: Path de entrada
        output_path: Path de salida
        preset: Preset de HandBrake
        
    Returns:
        Lista con comando y argumentos
        
    Raises:
        ValueError: Si los paths contienen caracteres peligrosos
    """
    # Validate paths before using in subprocess
    safe_input = validate_path(input_path)
    safe_output = validate_path(output_path)
    
    return [
        "HandBrakeCLI",
        "-i", str(safe_input),
        "-o", str(safe_output),
        "--preset=" + preset
    ]

def convert_mfs_to_mp4(input_path, output_path, preset=None):
    """
    Convierte un archivo .mfs a .mp4 usando HandBrakeCLI.
    
    Args:
        input_path: Ruta al archivo .mfs de entrada
        output_path: Ruta donde se guardará el archivo .mp4 de salida
        preset: Preset de HandBrake a usar (opcional)
        
    Returns:
        bool: True si la conversión fue exitosa, False en caso contrario
    """
    if preset is None:
        preset = config.HANDBRAKE_PRESET

    if not os.path.isfile(input_path):
        logger.error(f"archivo no encontrado path={short_path(input_path)}")
        return False

    try:
        command = build_handbrake_command(input_path, output_path, preset)
    except ValueError as e:
        logger.error(f"path invalido path={short_path(input_path)} err={e}")
        return False

    try:
        logger.info(f"convirtiendo path={short_path(input_path)}")
        # Capture output to avoid cluttering console unless debug
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        logger.info(f"convertido path={short_path(input_path)}")
        return True
    except subprocess.CalledProcessError as e:
        stderr_text = e.stderr.decode("utf-8", errors="replace") if e.stderr else ""
        # Best-effort redaction of absolute paths in tool output.
        try:
            stderr_text = stderr_text.replace(str(validate_path(input_path)), short_path(input_path))
            stderr_text = stderr_text.replace(str(validate_path(output_path)), short_path(output_path))
        except Exception:
            pass
        err = _one_line(stderr_text) if stderr_text else "unknown error"
        logger.error(f"fallo path={short_path(input_path)} err={err}")
        return False
    except FileNotFoundError:
        logger.error("handbrake no encontrado bin=HandBrakeCLI")
        return False
    except OSError as e:
        logger.error(f"handbrake fallo path={short_path(input_path)} err={type(e).__name__}")
        return False
