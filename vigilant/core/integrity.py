"""
Módulo de integridad forense para chain of custody.

Proporciona funciones para calcular hashes SHA-256 y generar metadata
de integridad para evidencia digital.
"""

from vigilant.core.runtime import require_cli
require_cli()

import hashlib
import json
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime, timezone


def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calcula SHA-256 de un archivo de forma eficiente.
    
    Args:
        file_path: Path al archivo
        chunk_size: Tamaño de chunks para lectura (8KB default)
    
    Returns:
        Hash SHA-256 en hexadecimal (64 caracteres)
    
    Raises:
        FileNotFoundError: Si el archivo no existe
        PermissionError: Si no hay permisos de lectura
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def generate_integrity_report(files: Dict[str, Path]) -> Dict[str, str]:
    """
    Genera reporte de integridad con hashes de múltiples archivos.
    
    Args:
        files: Dict con {label: path}
    
    Returns:
        Dict con {label: hash_sha256}
    
    Example:
        >>> files = {"original": Path("video.mfs"), "converted": Path("video.mp4")}
        >>> hashes = generate_integrity_report(files)
        >>> print(hashes)
        {'original': 'abc123...', 'converted': 'def456...'}
    """
    return {label: calculate_sha256(path) for label, path in files.items()}


def save_sha256_file(file_path: Path, hash_value: str, label: Optional[str] = None) -> Path:
    """
    Guarda hash SHA-256 en archivo de texto formato estándar.
    
    Args:
        file_path: Path del archivo original
        hash_value: Hash SHA-256 calculado
        label: Etiqueta opcional para el archivo
    
    Returns:
        Path del archivo .sha256 creado
    
    Example:
        >>> save_sha256_file(Path("video.mp4"), "abc123...")
        Path("video.mp4.sha256")
    """
    sha256_file = file_path.with_suffix(file_path.suffix + '.sha256')
    
    with open(sha256_file, 'w', encoding='utf-8') as f:
        if label:
            f.write(f"# {label}\n")
        f.write(f"{hash_value}  {file_path.name}\n")
    
    return sha256_file


def generate_conversion_metadata(
    source_path: Path,
    source_hash: str,
    converted_path: Path,
    converted_hash: str,
    conversion_tool: str = "HandBrake",
    preset: Optional[str] = None,
    command: Optional[str] = None,
    tool_version: Optional[str] = None,
    rescue_mode: Optional[bool] = None,
    rescue_details: Optional[Dict[str, Any]] = None,
    additional_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Genera metadata JSON completa de conversión para chain of custody.
    
    Args:
        source_path: Path del archivo original
        source_hash: SHA-256 del original
        converted_path: Path del archivo convertido
        converted_hash: SHA-256 del convertido
        conversion_tool: Nombre de herramienta de conversión
        preset: Preset usado (opcional)
        command: Comando ejecutado (opcional)
        tool_version: Versión de herramienta (opcional)
        rescue_mode: Indica si se usó modo rescate (opcional)
        rescue_details: Detalles del proceso de rescue (opcional)
        additional_data: Datos adicionales (opcional)
    
    Returns:
        Dict con metadata completa
    """
    conversion_data = {
        "tool": conversion_tool,
        "preset": preset,
        "command": command,
        "tool_version": tool_version,
        "rescue_mode": rescue_mode,
    }
    
    # Agregar rescue_details si rescue_mode está activo
    if rescue_mode and rescue_details:
        conversion_data["rescue_details"] = rescue_details
    
    metadata = {
        "integrity_version": "1.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": str(source_path),
            "filename": source_path.name,
            "sha256": source_hash,
            "size_bytes": source_path.stat().st_size if source_path.exists() else None,
        },
        "converted": {
            "path": str(converted_path),
            "filename": converted_path.name,
            "sha256": converted_hash,
            "size_bytes": converted_path.stat().st_size if converted_path.exists() else None,
        },
        "conversion": conversion_data
    }
    
    if additional_data:
        metadata["additional"] = additional_data
    
    return metadata


def save_metadata_json(metadata: Dict[str, Any], output_path: Path) -> Path:
    """
    Guarda metadata de integridad en archivo JSON.
    
    Args:
        metadata: Dict con metadata
        output_path: Path donde guardar el JSON
    
    Returns:
        Path del archivo JSON creado
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)
    
    return output_path


def verify_integrity(file_path: Path, expected_hash: str) -> bool:
    """
    Verifica integridad de un archivo comparando con hash esperado.
    
    Args:
        file_path: Path al archivo a verificar
        expected_hash: Hash SHA-256 esperado
    
    Returns:
        True si coincide, False si no
    """
    actual_hash = calculate_sha256(file_path)
    return actual_hash.lower() == expected_hash.lower()
