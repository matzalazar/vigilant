from vigilant.core.runtime import require_cli
require_cli()

import os
import shlex
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional
from vigilant.core.config import config
from vigilant.core.logger import logger, short_path

_BITEXACT_FLAGS = [
    "-map_metadata", "-1",
    "-map_chapters", "-1",
    "-fflags", "+bitexact",
    "-flags:v", "+bitexact",
    "-flags:a", "+bitexact",
]

def _read_header(path: Path, size: int = 512) -> bytes:
    """Lee los primeros bytes del archivo para análisis de codec."""
    try:
        with open(path, "rb") as f:
            return f.read(size)
    except OSError:
        return b""

def detect_codec_hint(path: Path) -> Optional[str]:
    """
    Detecta el codec de video analizando el encabezado del archivo.
    
    Returns:
        str | None: 'hevc', 'h264' o None si no se detecta
    """
    header = _read_header(path)
    header_lower = header.lower()
    if b"hevc" in header_lower or b"hvc1" in header_lower or b"hev1" in header_lower:
        return "hevc"
    if b"h264" in header_lower or b"avc1" in header_lower:
        return "h264"
    return None

def find_start_code_offset(path: Path) -> Optional[int]:
    """
    Busca el offset del primer start code de video (NAL unit).
    
    Returns:
        int | None: Offset en bytes o None si no se encuentra
    """
    patterns = (b"\x00\x00\x00\x01", b"\x00\x00\x01")  # Patrones de start code H.264/HEVC
    chunk_size = 1024 * 1024
    offset = 0
    tail = b""

    try:
        with open(path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                data = tail + chunk
                idx = -1
                for pat in patterns:
                    idx = data.find(pat)
                    if idx != -1:
                        break
                if idx != -1:
                    return offset - len(tail) + idx
                tail = data[-3:]
                offset += len(chunk)
    except OSError:
        return None

    return None

def _extract_from_offset(input_file: Path, offset: int) -> Optional[Path]:
    """
    Extrae el contenido del archivo desde un offset específico.
    
    Returns:
        Path | None: Ruta al archivo temporal extraído o None si falla
    """
    if offset <= 0:
        return None
    temp_dir = config.DATA_DIR / "tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix=f"{input_file.stem}_", suffix=".bin", dir=temp_dir)
    os.close(fd)

    try:
        with open(input_file, "rb") as src, open(temp_path, "wb") as dst:
            src.seek(offset)
            shutil.copyfileobj(src, dst, length=1024 * 1024)
        return Path(temp_path)
    except OSError:
        try:
            os.unlink(temp_path)
        except OSError:
            pass
        return None

def force_decode_with_codec(input_file: Path, output_file: Path, codec: str, start_offset: Optional[int] = None) -> dict:
    """Intenta decodificar forzando un codec específico (h264, hevc, etc)."""
    source = input_file
    extracted = None
    extraction_method = None
    if start_offset is not None:
        extracted = _extract_from_offset(input_file, start_offset)
        if extracted is not None:
            source = extracted
            extraction_method = "offset_copy"

    command = [
        "ffmpeg", "-y", "-f", codec, "-i", str(source),
        *_BITEXACT_FLAGS,
        str(output_file),
    ]
    success = False
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        success = True
    except subprocess.CalledProcessError:
        success = False
    finally:
        if extracted and extracted.exists():
            try:
                extracted.unlink()
            except OSError:
                pass

    return {
        "success": success,
        "command": command,
        "extraction_method": extraction_method,
        "extracted_path": str(extracted) if extracted else None,
    }

def force_decode_with_h264(input_file: Path, output_file: Path) -> bool:
    """Intenta decodificar forzando formato H.264."""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "h264", "-i", str(input_file),
            *_BITEXACT_FLAGS,
            str(output_file)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def force_decode_with_rawvideo(input_file: Path, output_file: Path) -> bool:
    """Ultima opción: intenta decodificar como video raw sin encapsulado."""
    try:
        subprocess.run([
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", config.RAW_PIX_FMT,
            "-s:v", config.RAW_RESOLUTION, "-r", str(config.RAW_FRAMERATE),
            "-i", str(input_file),
            *_BITEXACT_FLAGS,
            str(output_file)
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        return False

def try_force_decode(input_file: Path, output_file: Path) -> dict:
    """
    Pipeline de rescate de video: intenta múltiples estrategias de decodificación.
    
    Estrategia:
    1) Detectar codec por análisis de encabezado
    2) Buscar offset de start code
    3) Probar decodificación con codecs detectados/comunes
    4) Si todo falla, intentar rawvideo parametrizado
    
    Returns:
        dict: {
            "success": bool,
            "technique": str | None,  # "force_decode_hevc", "force_decode_h264", "rawvideo"
            "codec_hint": str | None,  # "hevc", "h264"
            "offset_found": bool,
            "offset_bytes": int | None,
            "command": str | None,  # Comando ejecutado (shell-escaped)
            "extraction_method": str | None,  # "offset_copy" si se usó extracción temporal
            "extracted_path": str | None,  # Path temporal si se usó extracción con offset
            "bitexact_flags": bool  # True si se aplicaron flags bitexact
        }
    """
    logger.info(f"rescate path={short_path(input_file)}")
    
    result = {
        "success": False,
        "technique": None,
        "codec_hint": None,
        "offset_found": False,
        "offset_bytes": None,
        "command": None,
        "extraction_method": None,
        "extracted_path": None,
        "bitexact_flags": False
    }
    
    codec_hint = detect_codec_hint(input_file)
    if codec_hint:
        logger.debug(f"rescate hint path={short_path(input_file)} codec={codec_hint}")
        result["codec_hint"] = codec_hint

    start_offset = find_start_code_offset(input_file)
    if start_offset is not None:
        logger.debug(f"rescate offset path={short_path(input_file)} offset={start_offset}")
        result["offset_found"] = True
        result["offset_bytes"] = start_offset
    else:
        logger.debug(f"rescate offset path={short_path(input_file)} offset=none")

    codecs_to_try = []
    if codec_hint:
        codecs_to_try.append(codec_hint)
    for codec in ("hevc", "h264"):
        if codec not in codecs_to_try:
            codecs_to_try.append(codec)

    for codec in codecs_to_try:
        logger.debug(f"rescate intento path={short_path(input_file)} codec={codec}")
        decode_result = force_decode_with_codec(input_file, output_file, codec, start_offset)
        if decode_result["success"]:
            logger.info(f"rescate ok path={short_path(input_file)}")
            result["success"] = True
            result["technique"] = f"force_decode_{codec}"

            result["command"] = shlex.join(decode_result["command"])
            result["extraction_method"] = decode_result["extraction_method"]
            if decode_result.get("extracted_path"):
                result["extracted_path"] = decode_result["extracted_path"]
            result["bitexact_flags"] = True
            return result

    logger.debug(f"rescate rawvideo path={short_path(input_file)}")
    if force_decode_with_rawvideo(input_file, output_file):
        logger.info(f"rescate ok path={short_path(input_file)}")
        result["success"] = True
        result["technique"] = "rawvideo"
        command = [
            "ffmpeg", "-y", "-f", "rawvideo", "-pix_fmt", config.RAW_PIX_FMT,
            "-s:v", config.RAW_RESOLUTION, "-r", str(config.RAW_FRAMERATE),
            "-i", str(input_file),
            *_BITEXACT_FLAGS,
            str(output_file),
        ]
        result["command"] = shlex.join(command)
        result["extraction_method"] = None
        result["bitexact_flags"] = True
        return result

    logger.error(f"rescate fallo path={short_path(input_file)}")
    return result
