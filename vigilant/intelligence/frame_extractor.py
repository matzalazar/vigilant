from __future__ import annotations

from vigilant.core.runtime import require_cli
require_cli()

import subprocess
from pathlib import Path
from typing import Optional, Tuple, Union

from vigilant.core.logger import logger, short_path

def _get_time_base(video_path: Path) -> Optional[float]:
    """
    Obtiene el time_base del video usando ffprobe.
    
    Returns:
        float | None: Time base en segundos por tick, o None si falla
    """
    command = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=time_base",
        "-of", "default=nw=1:nk=1",
        str(video_path),
    ]
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        time_base = result.stdout.strip()
        if not time_base or "/" not in time_base:
            return None
        num, den = time_base.split("/", 1)
        num_val = float(num)
        den_val = float(den)
        if den_val == 0:
            return None
        return num_val / den_val
    except Exception:
        return None

def _build_filter(filters: list[str]) -> str:
    """Construye una cadena de filtros ffmpeg separados por comas, ignorando strings vacíos."""
    return ",".join([f for f in filters if f])

def _extract_pts_from_name(path: Path) -> Optional[int]:
    """
    Extrae el PTS desde el nombre del frame (último segmento numérico).
    """
    parts = path.stem.split("_")
    for part in reversed(parts):
        if part.isdigit():
            try:
                return int(part)
            except ValueError:
                return None
    return None

def _frame_sort_key(path: Path) -> Tuple[int, Union[int, str]]:
    """
    Ordena por PTS numérico si está disponible, sino por nombre.
    """
    pts = _extract_pts_from_name(path)
    if pts is None:
        return (1, path.name)
    return (0, pts)

def _run_ffmpeg(video_path: Path, filter_str: str, output_pattern: Path) -> bool:
    """
    Ejecuta ffmpeg para extraer frames.
    
    Returns:
        bool: True si la extracción fue exitosa
    """
    command = ["ffmpeg", "-i", str(video_path)]
    if filter_str:
        command += ["-vf", filter_str]
    command += [
        "-fps_mode", "vfr",
        "-q:v", "2",
        "-frame_pts", "1",
        str(output_pattern),
    ]
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"frames fallo path={short_path(video_path)} err={e}")
        return False

def extract_frames(
    video_path: Path,
    output_dir: Path,
    interval_seconds: int = 5,
    mode: str = "interval",
    scene_threshold: float = 0.20,
    scale_width: int = 0,
) -> tuple[list[Path], Optional[float]]:
    """
    Extrae frames de un video usando ffmpeg.
    
    Args:
        video_path: Ruta al archivo de video
        output_dir: Directorio donde guardar los frames extraídos
        interval_seconds: Intervalo en segundos entre frames (modo interval)
        mode: Modo de extracción ('interval', 'scene', 'interval+scene')
        scene_threshold: Umbral de cambio de escena (0.0-1.0)
        scale_width: Ancho para redimensionar frames (0 = original)
    
    Returns:
        tuple: (lista de rutas a frames, time_base del video)
    """
    if not video_path.exists():
        logger.error(f"archivo no encontrado path={short_path(video_path)}")
        return [], None

    output_dir.mkdir(parents=True, exist_ok=True)
    time_base = _get_time_base(video_path)

    normalized = mode.replace("_", "+").replace(" ", "").lower()
    if normalized not in ("interval", "scene", "interval+scene"):
        normalized = "interval"

    def scale_filter() -> str:
        if scale_width > 0:
            return f"scale={scale_width}:-1"
        return ""

    def format_filter() -> str:
        # Avoid MJPEG errors with limited-range YUV
        return "format=yuvj420p"

    if normalized == "interval":
        filters = [f"fps=1/{interval_seconds}", scale_filter(), format_filter()]
        filter_str = _build_filter(filters)
        output_pattern = output_dir / f"{video_path.stem}_%d.jpg"
        logger.info(
            f"frames path={short_path(video_path)} modo=intervalo intervalo={interval_seconds}s escala={scale_width or 'orig'}"
        )
        if _run_ffmpeg(video_path, filter_str, output_pattern):
            frames = sorted(output_dir.glob(f"{video_path.stem}_*.jpg"), key=_frame_sort_key)
            if not frames:
                logger.warning(f"frames vacio path={short_path(video_path)}")
            else:
                logger.debug(f"frames ok path={short_path(video_path)} n={len(frames)}")
            return frames, time_base
        return [], time_base

    if normalized == "scene":
        scene_filter = f"select=gt(scene\\,{scene_threshold})"
        filters = [scene_filter, scale_filter(), format_filter()]
        filter_str = _build_filter(filters)
        output_pattern = output_dir / f"{video_path.stem}_%d.jpg"
        logger.info(
            f"frames path={short_path(video_path)} modo=escena umbral={scene_threshold} escala={scale_width or 'orig'}"
        )
        if _run_ffmpeg(video_path, filter_str, output_pattern):
            frames = sorted(output_dir.glob(f"{video_path.stem}_*.jpg"), key=_frame_sort_key)
            if not frames:
                logger.warning(
                    f"frames vacio path={short_path(video_path)} umbral={scene_threshold} "
                    "sugerencia=bajar_umbral_o_interval+scene"
                )
            else:
                logger.debug(f"frames ok path={short_path(video_path)} n={len(frames)}")
            return frames, time_base
        return [], time_base

    # interval+scene
    logger.info(
        f"frames path={short_path(video_path)} modo=intervalo+escena intervalo={interval_seconds}s umbral={scene_threshold} escala={scale_width or 'orig'}"
    )
    filters_interval = [f"fps=1/{interval_seconds}", scale_filter(), format_filter()]
    filters_scene = [f"select=gt(scene\\,{scene_threshold})", scale_filter(), format_filter()]
    output_interval = output_dir / f"{video_path.stem}_i_%d.jpg"
    output_scene = output_dir / f"{video_path.stem}_s_%d.jpg"
    _run_ffmpeg(video_path, _build_filter(filters_interval), output_interval)
    _run_ffmpeg(video_path, _build_filter(filters_scene), output_scene)

    frames = sorted(output_dir.glob(f"{video_path.stem}_*.jpg"), key=_frame_sort_key)
    unique_by_pts: dict[Union[int, str], Path] = {}
    for frame in frames:
        pts = _extract_pts_from_name(frame)
        key = pts if pts is not None else frame.name
        if key not in unique_by_pts:
            unique_by_pts[key] = frame
    deduped = sorted(unique_by_pts.values(), key=_frame_sort_key)
    if not deduped:
        logger.warning(
            f"frames vacio path={short_path(video_path)} umbral={scene_threshold} "
            "sugerencia=bajar_umbral_o_interval"
        )
    else:
        logger.debug(f"frames ok path={short_path(video_path)} n={len(deduped)}")
    return deduped, time_base
