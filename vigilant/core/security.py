"""
Módulo de seguridad para validación de inputs.

Proporciona funciones para validar paths y sanitizar inputs de usuario
antes de su uso en subprocess calls y otras operaciones sensibles.
"""

from vigilant.core.runtime import require_cli
require_cli()

from pathlib import Path
from typing import Union


# Caracteres peligrosos para command injection
DANGEROUS_CHARS = [';', '|', '&', '$', '`', '\n', '\r', '\0']


def validate_path(path: Union[Path, str]) -> Path:
    """
    Valida que un path sea seguro para uso en subprocess.
    
    Args:
        path: Path a validar (Path o string)
        
    Returns:
        Path resuelto y validado
        
    Raises:
        ValueError: Si el path contiene caracteres peligrosos
        
    Example:
        >>> safe_path = validate_path("/data/video.mp4")
        >>> # Falla con path malicioso:
        >>> validate_path("/data/video.mp4; rm -rf /")
        ValueError: Path inseguro (contiene ';'): ...
    """
    resolved = Path(path).resolve()
    path_str = str(resolved)
    
    for char in DANGEROUS_CHARS:
        if char in path_str:
            raise ValueError(
                f"Path inseguro (contiene '{repr(char)}'): {path_str}"
            )
    
    return resolved


def sanitize_prompt(prompt: str, max_len: int = 1000) -> str:
    """
    Sanitiza prompt de usuario para evitar injection attacks.
    
    Args:
        prompt: Prompt a sanitizar
        max_len: Longitud máxima permitida
        
    Returns:
        Prompt sanitizado (solo caracteres imprimibles, longitud limitada)
        
    Example:
        >>> sanitize_prompt("buscar persona\x00malicious")
        'buscar persona malicious'
    """
    # Remove control characters, keep only printable + whitespace
    sanitized = ''.join(
        c for c in prompt 
        if c.isprintable() or c.isspace()
    )
    
    # Limit length
    if len(sanitized) > max_len:
        sanitized = sanitized[:max_len]
    
    return sanitized.strip()


def validate_file_exists(path: Path) -> Path:
    """
    Valida que un archivo exista y sea accesible.
    
    Args:
        path: Path al archivo
        
    Returns:
        Path validado
        
    Raises:
        FileNotFoundError: Si el archivo no existe
        PermissionError: Si no hay permisos de lectura
    """
    if not path.exists():
        raise FileNotFoundError(f"Archivo no encontrado: {path}")
    
    if not path.is_file():
        raise ValueError(f"No es un archivo: {path}")
    
    # Check read permissions
    try:
        path.stat()
    except PermissionError:
        raise PermissionError(f"Sin permisos de lectura: {path}")
    
    return path
