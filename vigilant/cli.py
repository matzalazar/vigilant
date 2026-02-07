from __future__ import annotations

import os
os.environ["VIGILANT_CLI"] = "1"

import typer
from typing import Optional
import re
import time
import math
import shlex
import subprocess
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from vigilant import __version__
from vigilant.core.config import config
from vigilant.core.logger import logger, short_path
from vigilant.converters.handbrake import convert_mfs_to_mp4, build_handbrake_command
from vigilant.converters.rescue import try_force_decode
from vigilant.converters.ffmpeg import fallback_conversion_ffmpeg, normalize_container_metadata
from vigilant.parsers.pdf_parser import parse_pdf
from vigilant.intelligence.frame_extractor import extract_frames
from vigilant.intelligence.analyzer import AIAnalyzer
from vigilant.core.integrity import (
    calculate_sha256,
    save_sha256_file,
    generate_conversion_metadata,
    save_metadata_json
)
import json
import shutil

app = typer.Typer(help="Vigilant - Forensic Video Intelligence Suite", invoke_without_command=True)

def _check_binary(binary: str) -> tuple[bool, str]:
    path = shutil.which(binary)
    return (path is not None, path or "not found")

def _check_python_module(module: str) -> tuple[bool, str]:
    try:
        __import__(module)
        return True, "ok"
    except Exception as e:
        return False, f"{type(e).__name__}"

def _get_tool_version(command: list[str]) -> Optional[str]:
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=5)
        output = result.stdout.strip() or result.stderr.strip()
        if not output:
            return None
        return output.splitlines()[0].strip()
    except Exception:
        return None

def _run_system_check() -> bool:
    checks = []

    hb_ok, hb_detail = _check_binary("HandBrakeCLI")
    ff_ok, ff_detail = _check_binary("ffmpeg")
    fp_ok, fp_detail = _check_binary("ffprobe")
    fitz_ok, fitz_detail = _check_python_module("fitz")

    analyzer = AIAnalyzer()
    ollama_ok = analyzer.check_connection()
    ollama_detail = "ok" if ollama_ok else f"no connection to {config.OLLAMA_URL}"
    
    # Check if Ollama models are available
    if ollama_ok:
        models_ok, models_detail = analyzer.check_models()
    else:
        models_ok, models_detail = False, "ollama not available"

    yolo_needed = config.AI_FILTER_BACKEND == "yolo"
    if yolo_needed:
        yolo_mod_ok, yolo_mod_detail = _check_python_module("ultralytics")
        yolo_model_ok = bool(config.YOLO_MODEL and Path(config.YOLO_MODEL).exists())
        yolo_model_detail = str(config.YOLO_MODEL) if config.YOLO_MODEL else "VIGILANT_YOLO_MODEL not set"
    else:
        yolo_mod_ok, yolo_mod_detail = True, "not required"
        yolo_model_ok, yolo_model_detail = True, "not required"

    convert_ok = hb_ok and ff_ok
    parse_ok = fitz_ok
    analyze_ok = ff_ok and fp_ok and ollama_ok and models_ok and yolo_mod_ok and yolo_model_ok

    checks.append(("HandBrakeCLI", hb_ok, hb_detail))
    checks.append(("ffmpeg", ff_ok, ff_detail))
    checks.append(("ffprobe", fp_ok, fp_detail))
    checks.append(("PyMuPDF (fitz)", fitz_ok, fitz_detail))
    checks.append(("Ollama", ollama_ok, ollama_detail))
    checks.append(("Ollama models", models_ok, models_detail))
    if yolo_needed:
        checks.append(("ultralytics (YOLO)", yolo_mod_ok, yolo_mod_detail))
        checks.append(("YOLO model path", yolo_model_ok, yolo_model_detail))

    typer.echo("Componentes del sistema:")
    for name, ok, detail in checks:
        status = "OK" if ok else "FAIL"
        typer.echo(f"- {name}: {status} ({detail})")

    typer.echo("")
    typer.echo(f"convert: {'OK' if convert_ok else 'FAIL'}")
    typer.echo(f"parse: {'OK' if parse_ok else 'FAIL'}")
    typer.echo(f"analyze: {'OK' if analyze_ok else 'FAIL'}")

    return convert_ok and parse_ok and analyze_ok

def version_callback(value: bool) -> None:
    """Muestra la versión y sale."""
    if value:
        typer.echo(f"Vigilant v{__version__}")
        raise typer.Exit()

@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Muestra la versión del programa"
    ),
    check: Optional[bool] = typer.Option(
        None,
        "--check",
        is_eager=True,
        help="Verifica dependencias externas y estado del entorno"
    ),
) -> None:
    """Vigilant - Forensic Video Intelligence Suite"""
    if check:
        ok = _run_system_check()
        raise typer.Exit(code=0 if ok else 1)

def get_video_duration(video_path: Path) -> Optional[float]:
    """
    Obtiene la duración de un video en segundos usando ffprobe.
    
    Returns:
        float: Duración en segundos, o None si falla
    """
    try:
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0 and result.stdout.strip():
            return float(result.stdout.strip())
    except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
        pass
    return None

def format_duration(seconds: float) -> str:
    """
    Formatea duración en segundos a HH:MM:SS.
    """
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

def _safe_prompt_display(text: str, max_len: int = 200) -> str:
    """
    Normaliza el prompt para mostrar en reportes sin caracteres de control ni longitud excesiva.
    """
    cleaned = re.sub(r"[\x00-\x1f\x7f]+", " ", text)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if len(cleaned) > max_len:
        return cleaned[: max_len - 3] + "..."
    return cleaned

def _safe_slug(text: str, max_len: int = 80) -> str:
    """
    Convierte un texto a un slug seguro para nombres de archivo.
    """
    slug = re.sub(r"[^\w\.-]+", "_", text.strip())
    slug = slug.strip("_")
    if not slug:
        return "analysis"
    if len(slug) > max_len:
        digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:8]
        base = slug[: max_len - 9].rstrip("_")
        return f"{base}_{digest}" if base else digest
    return slug

_NEGATIVE_ANALYSIS_PATTERNS = [
    r"\bno\s+se\s+observa\b",
    r"\bno\s+se\s+ve\b",
    r"\bno\s+se\s+detecta\b",
    r"\bno\s+aparece\b",
    r"\bno\s+hay\b",
    r"\bno\s+coincide\b",
    r"\bno\s+corresponde\b",
    r"\bno\s+vehicle\b",
    r"\bno\s+car\b",
    r"\bno\s+person\b",
    r"\bnot\s+visible\b",
    r"\bnot\s+present\b",
    r"\bdoes\s+not\s+match\b",
]

_REPORT_SECTION_RE = re.compile(
    r"^(Hechos Observables|Coincidencias relevantes|Observaciones|Limitaciones)\s*:?\s*$",
    re.IGNORECASE,
)

_UNVERIFIED_REPORT_PATTERNS = [
    r"sentido de circulaci[oó]n",
    r"direcci[oó]n opuesta",
    r"ausencia de otros",
    r"único objeto",
    r"unico objeto",
    r"frames consecutiv",
    r"\bocasiones\b",
]

def _analysis_contradicts_match(text: str) -> bool:
    """
    Detecta negaciones explícitas en el análisis IA para evitar falsos positivos en el reporte.
    """
    if not text:
        return False
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in _NEGATIVE_ANALYSIS_PATTERNS)

def _should_drop_report_line(line: str) -> bool:
    """
    Filtra líneas del reporte IA que contienen afirmaciones no verificables o datos sensibles.
    """
    low = line.lower()
    if "tiempo de duracion" in low or "tiempo de duración" in low:
        return True
    if "duracion" in low or "duración" in low:
        return True
    if re.search(r"\btiempo\b.*\b\d{1,2}:\d{2}(:\d{2})?\b", low):
        return True
    return any(re.search(pattern, low) for pattern in _UNVERIFIED_REPORT_PATTERNS)

def _sanitize_ai_report(report_text: str) -> str:
    """
    Limpia el reporte IA eliminando líneas que suelen introducir datos no verificables.
    """
    if not report_text:
        return report_text

    # Preserve known safe fallback messages (not model-generated narrative).
    raw = report_text.strip()
    lowered_raw = raw.lower()
    if lowered_raw.startswith("no se detectaron coincidencias"):
        return raw
    if lowered_raw.startswith("no se pudo generar el informe"):
        return raw

    lines = report_text.splitlines()
    filtered: list[str] = []
    pending_section: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue

        match = _REPORT_SECTION_RE.match(stripped)
        if match:
            section = match.group(1)
            pending_section = section[0].upper() + section[1:]
            continue

        if not stripped.startswith("-"):
            # Solo conservar bullets bajo secciones conocidas
            continue

        if _should_drop_report_line(stripped):
            continue

        if pending_section:
            if filtered and filtered[-1] != "":
                filtered.append("")
            filtered.append(f"{pending_section}:")
            pending_section = None

        filtered.append(stripped)

    if filtered:
        last = filtered[-1].rstrip()
        if last and last[-1] not in ".!?:)" and len(last) > 40:
            filtered = filtered[:-1]

    sanitized = "\n".join(filtered).strip()
    if not sanitized:
        return "Informe no disponible (contenido descartado por sanitización)."
    return sanitized

def _extract_pts_from_frame_name(frame_path: Path) -> Optional[int]:
    """
    Extrae el PTS desde el nombre del frame (último segmento numérico).
    """
    parts = frame_path.stem.split("_")
    for part in reversed(parts):
        if part.isdigit():
            try:
                return int(part)
            except ValueError:
                return None
    return None

def _write_integrity_files(
    source_path: Path,
    output_path: Path,
    conversion_tool: str,
    preset: Optional[str] = None,
    command: Optional[str] = None,
    tool_version: Optional[str] = None,
    rescue_mode: Optional[bool] = None,
    rescue_details: Optional[dict] = None,
) -> None:
    """
    Genera hashes y metadata de integridad para cualquier salida convertida.
    """
    hash_source = calculate_sha256(source_path)
    hash_converted = calculate_sha256(output_path)

    logger.info(f"hash original={hash_source[:16]}... archivo={short_path(source_path)}")
    logger.info(f"hash convertido={hash_converted[:16]}... archivo={short_path(output_path)}")

    save_sha256_file(output_path, hash_converted, label="Converted Video")

    metadata = generate_conversion_metadata(
        source_path=source_path,
        source_hash=hash_source,
        converted_path=output_path,
        converted_hash=hash_converted,
        conversion_tool=conversion_tool,
        preset=preset,
        command=command,
        tool_version=tool_version,
        rescue_mode=rescue_mode,
        rescue_details=rescue_details,
    )

    metadata_file = output_path.with_suffix(output_path.suffix + ".integrity.json")
    save_metadata_json(metadata, metadata_file)
    logger.info(f"integridad guardada path={short_path(metadata_file)}")

@app.command()
def convert(
    input_dir: Path = typer.Option(config.INPUT_MFS_DIR, help="Directory containing .mfs files"),
    output_dir: Path = typer.Option(config.OUTPUT_MP4_DIR, help="Directory to save .mp4 files"),
    rescue: bool = typer.Option(True, help="Attempt to rescue failed conversions")
):
    """
    Batch convert .mfs files to .mp4.
    """
    if not input_dir.exists():
        logger.error(f"input missing path={short_path(input_dir)}")
        raise typer.Exit(code=1)

    output_dir.mkdir(parents=True, exist_ok=True)
    
    for file_path in input_dir.rglob("*.mfs"):
        # Calculate relative path to maintain structure
        relative_path = file_path.relative_to(input_dir)
        output_file = output_dir / relative_path.with_suffix(".mp4")
        
        # Ensure parent directory exists in output
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_file.exists():
            logger.info(f"omitido path={short_path(output_file)}")
            continue
            
        try:
            handbrake_command = build_handbrake_command(file_path, output_file, config.HANDBRAKE_PRESET)
        except ValueError as e:
            logger.error(f"path invalido path={short_path(file_path)} err={e}")
            continue
        handbrake_version = _get_tool_version(["HandBrakeCLI", "--version"])
        ffmpeg_version = _get_tool_version(["ffmpeg", "-version"])
        success = convert_mfs_to_mp4(file_path, output_file)
        if success:
            normalized_tmp = output_file.with_name(output_file.stem + "_normalized" + output_file.suffix)
            try:
                if normalize_container_metadata(output_file, normalized_tmp):
                    normalize_command = [
                        "ffmpeg", "-y", "-i", str(output_file),
                        "-map_metadata", "-1",
                        "-map_chapters", "-1",
                        "-fflags", "+bitexact",
                        "-flags:v", "+bitexact",
                        "-flags:a", "+bitexact",
                        "-c", "copy", str(normalized_tmp),
                    ]
                    normalized_tmp.replace(output_file)
                else:
                    normalize_command = None
            finally:
                # Always cleanup temp file if it exists
                if normalized_tmp.exists():
                    normalized_tmp.unlink()
            try:
                handbrake_cmd = shlex.join(handbrake_command)
                normalize_cmd = shlex.join(normalize_command) if normalize_command else None
                combined_command = f"{handbrake_cmd} && {normalize_cmd}" if normalize_cmd else handbrake_cmd
                if normalize_command:
                    combined_version = "; ".join(
                        [v for v in [handbrake_version, ffmpeg_version] if v]
                    ) or None
                else:
                    combined_version = handbrake_version
                _write_integrity_files(
                    source_path=file_path,
                    output_path=output_file,
                    conversion_tool="HandBrake+ffmpeg normalize" if normalize_command else "HandBrake",
                    preset=config.HANDBRAKE_PRESET,
                    command=combined_command,
                    tool_version=combined_version,
                    rescue_mode=False,
                )
            except Exception as e:
                logger.warning(f"fallo calculo hash path={short_path(output_file)} err={e}")
            continue

        if rescue:
            logger.info(f"fallo path={short_path(file_path)} rescate=si")

            # Try simple ffmpeg remux first (keeps original structure)
            ffmpeg_version = _get_tool_version(["ffmpeg", "-version"])
            if fallback_conversion_ffmpeg(file_path, output_file):
                try:
                    remux_command = [
                        "ffmpeg", "-y", "-i", str(file_path),
                        "-map_metadata", "-1",
                        "-map_chapters", "-1",
                        "-fflags", "+bitexact",
                        "-flags:v", "+bitexact",
                        "-flags:a", "+bitexact",
                        "-c", "copy", str(output_file),
                    ]
                    _write_integrity_files(
                        source_path=file_path,
                        output_path=output_file,
                        conversion_tool="ffmpeg remux",
                        command=shlex.join(remux_command),
                        tool_version=ffmpeg_version,
                        rescue_mode=True,
                    )
                except Exception as e:
                    logger.warning(f"fallo calculo hash path={short_path(output_file)} err={e}")
                continue


            forced_output = output_file.with_name(output_file.stem + "_forced.mp4")
            rescue_result = try_force_decode(file_path, forced_output)
            if rescue_result["success"]:
                try:
                    # Preparar rescue_details para metadata
                    rescue_details = {
                        "technique": rescue_result["technique"],
                        "codec_hint": rescue_result["codec_hint"],
                        "offset_found": rescue_result["offset_found"],
                        "extraction_method": rescue_result["extraction_method"],
                        "bitexact_flags": rescue_result["bitexact_flags"]
                    }
                    if rescue_result["offset_bytes"] is not None:
                        rescue_details["offset_bytes"] = rescue_result["offset_bytes"]
                    if rescue_result.get("extracted_path"):
                        rescue_details["extracted_path"] = rescue_result["extracted_path"]
                    
                    _write_integrity_files(
                        source_path=file_path,
                        output_path=forced_output,
                        conversion_tool="ffmpeg rescue",
                        command=rescue_result["command"],  # Comando real ejecutado
                        tool_version=ffmpeg_version,
                        rescue_mode=True,
                        rescue_details=rescue_details,
                    )
                except Exception as e:
                    logger.warning(f"fallo calculo hash path={short_path(forced_output)} err={e}")


@app.command()
def parse(
    input_dir: Path = typer.Option(config.INPUT_PDF_DIR, help="Directory containing .pdf reports"),
    output_dir: Path = typer.Option(config.OUTPUT_JSON_DIR, help="Directory to save .json files")
):
    """
    Parse PDF reports into JSON.
    """
    if not input_dir.exists():
        logger.error(f"input missing path={short_path(input_dir)}")
        raise typer.Exit(code=1)

    output_dir.mkdir(parents=True, exist_ok=True)

    for pdf_file in input_dir.glob("*.pdf"):
        try:
            report = parse_pdf(pdf_file)
            logger.info(f"parseado path={short_path(pdf_file)}")
            
            output_file = output_dir / (pdf_file.stem + ".json")
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(report, f, indent=4, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"parseo fallo path={short_path(pdf_file)} err={e}")

@app.command()
def analyze(
    input_dir: Path = typer.Option(config.OUTPUT_MP4_DIR, help="Directory containing .mp4 files to analyze"),
    input_file: Optional[Path] = typer.Option(None, "--video", "--file", help="Path to a single .mp4 file to analyze"),
    prompt: str = typer.Option(..., help="Natural language prompt for search (e.g. 'Person with red jacket')"),
    cleanup: bool = typer.Option(True, help="Delete extracted frames after analysis")
):
    """
    Analyze videos using AI to find specific objects/people.
    """
    analyzer = AIAnalyzer()
    if not analyzer.check_connection():
        logger.error("ollama no disponible")
        raise typer.Exit(code=1)
    filter_backend = config.AI_FILTER_BACKEND
    if filter_backend not in ("llava", "yolo"):
        logger.warning(f"prefiltro desconocido '{filter_backend}', usando llava")
        filter_backend = "llava"
    if filter_backend == "yolo" and not analyzer.check_yolo():
        logger.error("yolo no disponible")
        raise typer.Exit(code=1)

    logger.info(f"analisis inicio model={config.AI_ANALYSIS_MODEL}")
    logger.info(f"prefiltro backend={filter_backend}")
    if filter_backend == "yolo":
        logger.info(
            f"prefiltro yolo model={config.YOLO_MODEL} conf={config.YOLO_CONFIDENCE} iou={config.YOLO_IOU}"
        )
    else:
        logger.info(f"prefiltro model={config.AI_FILTER_MODEL} min_conf={config.AI_FILTER_MIN_CONFIDENCE}")
    logger.info(f"analisis profundo model={config.AI_ANALYSIS_MODEL}")
    logger.info(f"reporte model={config.AI_REPORT_MODEL}")
    if config.AI_USE_EMBEDDINGS:
        logger.info(f"embeddings model={config.AI_EMBED_MODEL} umbral={config.AI_EMBED_THRESHOLD}")
    if getattr(config, "SCENARIO_PROFILE", ""):
        logger.info(f"escenario perfil={config.SCENARIO_PROFILE}")
    elif getattr(config, "SCENARIO", None):
        logger.info(f"escenario datos={config.SCENARIO}")
    logger.info(
        f"frames modo={config.FRAME_MODE} intervalo={config.AI_SAMPLE_INTERVAL}s "
        f"umbral_escena={config.FRAME_SCENE_THRESHOLD} escala={config.FRAME_SCALE or 'orig'}"
    )
    logger.debug(f"prompt text='{prompt}'")  # Contenido sensible en DEBUG

    motion_enabled = filter_backend == "yolo" and config.MOTION_ENABLE
    motion_keywords = config.MOTION_KEYWORDS
    if isinstance(motion_keywords, str):
        motion_keywords_list = [k.strip().lower() for k in motion_keywords.split(",") if k.strip()]
    elif isinstance(motion_keywords, list):
        motion_keywords_list = [str(k).strip().lower() for k in motion_keywords if str(k).strip()]
    else:
        motion_keywords_list = []

    def prompt_requires_motion(prompt_text: str) -> bool:
        if not motion_enabled:
            return False
        if not config.MOTION_REQUIRE_KEYWORDS:
            return True
        prompt_lower = prompt_text.lower()
        return any(keyword in prompt_lower for keyword in motion_keywords_list)

    motion_required = prompt_requires_motion(prompt)
    if motion_enabled and motion_required:
        logger.info(
            f"movimiento activo min_px={config.MOTION_MIN_DISPLACEMENT} min_frames={config.MOTION_MIN_FRAMES}"
        )

    display_prompt = _safe_prompt_display(prompt)
    report_lines = [f"# Vigilant Analysis Report", f"**Prompt:** {display_prompt}"]
    report_items = []

    def format_timestamp(frame_path: Path, frame_index: int, interval: int, time_base: Optional[float]) -> str:
        """
        Calcula timestamp aproximado basándose en el índice del frame.
        
        Args:
            frame_path: Path al frame
            frame_index: Índice del frame (1-indexed)
            interval: Intervalo de extracción en segundos
            time_base: Time base del video (opcional, no usado actualmente)
        
        Note:
            El PTS en el nombre del frame es un índice secuencial de ffmpeg,
            no el PTS real en unidades de time_base. Por lo tanto, usamos
            el índice del frame multiplicado por el intervalo para calcular
            el timestamp aproximado.
        """
        # Calcular segundos basándose en el índice de frame
        # frame_index es 1-indexed, así que frame 1 = 0s, frame 2 = interval*1s, etc.
        seconds = max(0.0, (frame_index - 1) * interval)
        return format_duration(seconds)

    if input_file:
        if not input_file.exists() or not input_file.is_file():
            logger.error(f"archivo no encontrado path={short_path(input_file)}")
            raise typer.Exit(code=1)
        video_files = [input_file]
    else:
        video_files = list(input_dir.rglob("*.mp4"))

    if not video_files:
        logger.info("no hay videos para analizar")
        return

    for video_file in video_files:
        logger.info(f"analizando path={short_path(video_file)}")
        
        # Calcular hash de integridad del video
        try:
            video_hash = calculate_sha256(video_file)
            logger.info(f"hash video={video_hash[:16]}... archivo={short_path(video_file)}")
        except Exception as e:
            logger.warning(f"fallo calculo hash path={short_path(video_file)} err={e}")
            video_hash = None
        
        # Obtener duración del video
        video_duration = get_video_duration(video_file)
        
        # Temp dir for this video's frames (inside data/tmp)
        frames_dir = config.DATA_DIR / "tmp" / video_file.stem
        frames, time_base = extract_frames(
            video_file,
            frames_dir,
            interval_seconds=config.AI_SAMPLE_INTERVAL,
            mode=config.FRAME_MODE,
            scene_threshold=config.FRAME_SCENE_THRESHOLD,
            scale_width=config.FRAME_SCALE,
        )
        total_frames = len(frames)
        show_progress = input_file is not None and total_frames > 0
        if show_progress:
            video_start = time.monotonic()

        hits = []
        prev_centers: list[tuple[float, float]] = []
        motion_streak = 0
        for idx, frame in enumerate(frames, start=1):
            frame_start = time.monotonic()
            try:
                # Analysis logic - wrapped in try-except for robustness
                if filter_backend == "yolo":
                    quick = analyzer.yolo_match(frame, prompt)
                    min_conf = config.YOLO_CONFIDENCE
                else:
                    quick = analyzer.quick_match(frame, prompt)
                    min_conf = config.AI_FILTER_MIN_CONFIDENCE

                if not quick["match"]:
                    if motion_required:
                        motion_streak = 0
                        prev_centers = []
                    continue
                if quick["confidence"] < min_conf:
                    if motion_required:
                        motion_streak = 0
                        prev_centers = []
                    continue

                if motion_required and filter_backend == "yolo":
                    detections = quick.get("detections", [])
                    centers = []
                    for det in detections:
                        xyxy = det.get("xyxy")
                        if not xyxy or len(xyxy) != 4:
                            continue
                        x1, y1, x2, y2 = xyxy
                        centers.append(((x1 + x2) / 2.0, (y1 + y2) / 2.0))

                    movement_detected = False
                    if prev_centers and centers:
                        for cx, cy in centers:
                            for px, py in prev_centers:
                                dist = math.hypot(cx - px, cy - py)
                                if dist >= config.MOTION_MIN_DISPLACEMENT:
                                    movement_detected = True
                                    break
                            if movement_detected:
                                break

                    if movement_detected:
                        motion_streak += 1
                    else:
                        motion_streak = 0

                    prev_centers = centers

                    if motion_streak < config.MOTION_MIN_FRAMES:
                        continue

                similarity = None
                if config.AI_USE_EMBEDDINGS:
                    similarity = analyzer.prompt_similarity(prompt, quick["detail"])
                    if similarity is not None and similarity < config.AI_EMBED_THRESHOLD:
                        continue

                # Enriquecer prompt con contexto de movimiento si está activo
                enriched_prompt = prompt
                if motion_required and motion_streak >= config.MOTION_MIN_FRAMES:
                    enriched_prompt = (
                        f"{prompt}. CONTEXTO: El objeto está en movimiento activo "
                        f"(detectado por {motion_streak} frames consecutivos)."
                    )
                    logger.debug(f"prompt enriquecido con contexto de movimiento frames={motion_streak}")

                deep = analyzer.deep_analyze(frame, enriched_prompt)
                if _analysis_contradicts_match(deep.get("text", "")):
                    logger.info(
                        f"hit descartado (negacion en analisis) frame={idx} path={short_path(frame)}"
                    )
                    continue
                timestamp = format_timestamp(frame, idx, config.AI_SAMPLE_INTERVAL, time_base)
                logger.debug(f"hit path=/{frame.name} text='{deep['text']}'")  # Análisis IA en DEBUG
                hit = {
                    "image_path": deep["image_path"],
                    "detail": quick["detail"],
                    "analysis": deep["text"],
                    "confidence": quick["confidence"],
                    "similarity": similarity if similarity is not None else 0.0,
                    "frame_index": idx,
                    "timestamp": timestamp,
                    "motion_required": motion_required,
                }
                hits.append(hit)
                
            except Exception as e:
                # Log error but continue with next frame instead of crashing
                logger.error(f"fallo analisis frame={idx} path={short_path(frame)} err={e}")
                continue
                
            finally:
                if show_progress:
                    elapsed = time.monotonic() - video_start
                    frame_elapsed = time.monotonic() - frame_start
                    fps = (idx / elapsed) if elapsed > 0 else 0.0
                    logger.info(
                        f"procesado {idx}/{total_frames} "
                        f"tiempo_frame={frame_elapsed:.2f}s "
                        f"velocidad={fps:.2f} fps"
                    )

        if hits:
            report_lines.append(f"## Video: `{video_file.name}`")
            if video_hash:
                report_lines.append(f"**SHA-256**: `{video_hash}`")
            if video_duration:
                report_lines.append(f"**Duración:** {format_duration(video_duration)}")
            report_lines.append(f"**Frames analizados:** {total_frames}")
            report_lines.append("")
            
            for hit in hits:
                # Copy hit image to reports/imgs dir
                report_images_dir = config.DATA_DIR / "reports" / "imgs"
                report_images_dir.mkdir(parents=True, exist_ok=True)
                
                src = Path(hit["image_path"])
                dest = report_images_dir / src.name
                shutil.copy2(src, dest)

                frame_idx = hit.get("frame_index", 1)
                timestamp = hit.get("timestamp") or format_timestamp(src, frame_idx, config.AI_SAMPLE_INTERVAL, time_base)
                
                report_lines.append(f"- **Hit**: {hit['analysis']}")
                report_lines.append(f"  - Frame: {frame_idx}/{total_frames}")
                report_lines.append(f"  - Timestamp: {timestamp}")
                report_lines.append(f"  - Prefiltro: {hit['detail']} (conf {hit['confidence']:.0%})")
                if config.AI_USE_EMBEDDINGS:
                    report_lines.append(f"  - Similaridad: {hit['similarity']:.2f}")
                if hit.get("motion_required"):
                    report_lines.append("  - Movimiento: confirmado")
                report_lines.append(f"  - Image: `../imgs/{dest.name}`")
                report_lines.append(f"  ![Hit](../imgs/{dest.name})")

                report_items.append({
                    "video": video_file.name,
                    "timestamp": timestamp,
                    "detail": hit["detail"],
                    "analysis": hit["analysis"],
                    "confidence": hit["confidence"],
                    "similarity": hit["similarity"],
                })
            report_lines.append("")

        if cleanup and frames_dir.exists():
            shutil.rmtree(frames_dir)

    # Generate legal-style report
    report_text = analyzer.generate_report(prompt, report_items)
    report_text = _sanitize_ai_report(report_text)
    if report_text.startswith("Informe no disponible"):
        logger.warning("informe ia descartado por sanitizacion")
    warning_lines = [
        "",
        "> [!WARNING]",
        "> **Timestamps Aproximados**: Los timestamps mostrados son estimaciones basadas en índice de frame × intervalo de extracción.",
        "> En modo `scene` o `interval+scene`, pueden tener margen de error de varios segundos respecto al tiempo real del video.",
        "> Para timestamps precisos al segundo, verificar con reproductor de video o usar solo modo `interval`.",
        "",
        "## Informe juridico (IA)",
        report_text,
        "",
    ]
    report_lines[2:2] = warning_lines

    # Save report to reports/md
    report_slug = _safe_slug(prompt)
    report_timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    report_path = config.DATA_DIR / "reports" / "md" / f"analysis_{report_slug}_{report_timestamp}.md"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write("\n".join(report_lines))
    
    logger.info(f"analisis ok path=/{report_path.name}")

if __name__ == "__main__":
    app()
