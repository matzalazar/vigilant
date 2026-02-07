from __future__ import annotations

from vigilant.core.runtime import require_cli
require_cli()

import os
from pathlib import Path
from typing import Any, Optional

import yaml
from dotenv import load_dotenv

# Cargar variables de entorno desde archivo .env si está presente
load_dotenv()

def _deep_merge(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    """Fusiona dos diccionarios recursivamente, priorizando valores de override."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def _apply_scenario_config(data: dict[str, Any]) -> dict[str, Any]:
    """
    Aplica overrides de configuración basados en el primer perfil de escenario coincidente.
    
    Returns:
        dict: Configuración con overrides aplicados si hay coincidencia
    """
    scenario = data.get("scenario")
    profiles = data.get("profiles")
    if not isinstance(scenario, dict) or not isinstance(profiles, list):
        return data

    for profile in profiles:
        if not isinstance(profile, dict):
            continue
        match = profile.get("match")
        overrides = profile.get("overrides")
        if not isinstance(match, dict) or not isinstance(overrides, dict):
            continue
        if all(scenario.get(key) == value for key, value in match.items()):
            merged = _deep_merge(data, overrides)
            merged["_profile_applied"] = profile.get("name", "profile")
            return merged
    return data

def _load_yaml_config(base_dir: Path) -> dict[str, Any]:
    """
    Carga configuración desde archivos YAML (default.yaml luego local.yaml).
    
    Returns:
        dict: Configuración fusionada con escenarios aplicados
    """
    config_dir = base_dir / "config"
    data: dict[str, Any] = {}
    for name in ("default.yaml", "local.yaml"):
        path = config_dir / name
        if not path.exists():
            continue
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = yaml.safe_load(f) or {}
                if isinstance(content, dict):
                    data = _deep_merge(data, content)
        except OSError:
            continue
    return _apply_scenario_config(data)

def _get_nested(data: dict[str, Any], path: str) -> Any:
    """Obtiene un valor anidado de un diccionario usando notación de punto (ej: 'ai.model')."""
    current: Any = data
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current

def _to_bool(value: Any, default: bool = False) -> bool:
    """Convierte un valor a booleano con valor por defecto."""
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in ("1", "true", "yes", "y", "on")
    return default

def _to_int(value: Any, default: int) -> int:
    """Convierte un valor a entero con valor por defecto."""
    if value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

def _to_float(value: Any, default: float) -> float:
    """Convierte un valor a float con valor por defecto."""
    if value is None:
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default

class Config:
    def __init__(self) -> None:
        self.BASE_DIR = Path(__file__).resolve().parents[2]
        if not (self.BASE_DIR / "config").exists():
            package_base = Path(__file__).resolve().parents[1]
            if (package_base / "config").exists():
                self.BASE_DIR = package_base
        self.CONFIG_DIR = self.BASE_DIR / "config"
        self._yaml = _load_yaml_config(self.BASE_DIR)

        def env_or_yaml(env_keys: list[str], yaml_path: str, default: Any) -> Any:
            for key in env_keys:
                value = os.getenv(key)
                if value is not None and value != "":
                    return value
            value = _get_nested(self._yaml, yaml_path)
            return value if value is not None else default

        def resolve_path(value: Any, default: Path) -> Path:
            raw = value if value is not None else default
            path = Path(raw)
            if not path.is_absolute():
                return self.BASE_DIR / path
            return path

        # Rutas de directorios
        data_dir = env_or_yaml(["VIGILANT_DATA_DIR", "MFS_DATA_DIR"], "paths.data_dir", self.BASE_DIR / "data")
        self.DATA_DIR = resolve_path(data_dir, self.BASE_DIR / "data")

        input_mfs = env_or_yaml(
            ["VIGILANT_INPUT_DIR", "MFS_INPUT_DIR"],
            "paths.input_mfs_dir",
            self.DATA_DIR / "mfs",
        )
        self.INPUT_MFS_DIR = resolve_path(input_mfs, self.DATA_DIR / "mfs")

        output_mp4 = env_or_yaml(
            ["VIGILANT_OUTPUT_DIR", "MFS_OUTPUT_DIR"],
            "paths.output_mp4_dir",
            self.DATA_DIR / "mp4",
        )
        self.OUTPUT_MP4_DIR = resolve_path(output_mp4, self.DATA_DIR / "mp4")

        input_pdf = env_or_yaml(
            ["VIGILANT_INPUT_PDF_DIR"],
            "paths.input_pdf_dir",
            self.DATA_DIR / "pdf",
        )
        self.INPUT_PDF_DIR = resolve_path(input_pdf, self.DATA_DIR / "pdf")

        output_json = env_or_yaml(
            ["VIGILANT_OUTPUT_JSON_DIR"],
            "paths.output_json_dir",
            self.DATA_DIR / "json",
        )
        self.OUTPUT_JSON_DIR = resolve_path(output_json, self.DATA_DIR / "json")

        logs_dir = env_or_yaml(
            ["VIGILANT_LOGS_DIR"],
            "paths.logs_dir",
            self.BASE_DIR / "logs",
        )
        self.LOGS_DIR = resolve_path(logs_dir, self.BASE_DIR / "logs")

        # Configuración de logging
        log_level = env_or_yaml(["VIGILANT_LOG_LEVEL"], "logging.level", "INFO")
        self.LOG_LEVEL = str(log_level).upper()

        # Configuración por defecto de HandBrake
        preset = env_or_yaml(
            ["VIGILANT_HANDBRAKE_PRESET", "MFS_HANDBRAKE_PRESET"],
            "handbrake.preset",
            "Fast 1080p30",
        )
        self.HANDBRAKE_PRESET = str(preset)

        # AI Intelligence Settings
        ai_model = env_or_yaml(["VIGILANT_AI_MODEL"], "ai.model", "llava")
        self.AI_MODEL = str(ai_model)
        self.AI_FILTER_MODEL = str(env_or_yaml(["VIGILANT_FILTER_MODEL"], "ai.filter_model", self.AI_MODEL))
        self.AI_ANALYSIS_MODEL = str(env_or_yaml(["VIGILANT_ANALYSIS_MODEL"], "ai.analysis_model", self.AI_MODEL))
        self.AI_REPORT_MODEL = str(env_or_yaml(["VIGILANT_REPORT_MODEL"], "ai.report_model", "mistral:latest"))
        self.AI_EMBED_MODEL = str(env_or_yaml(["VIGILANT_EMBED_MODEL"], "ai.embed_model", "nomic-embed-text:latest"))
        self.AI_PROMPT_FILTER = str(env_or_yaml(["VIGILANT_PROMPT_FILTER"], "ai.prompts.filter", ""))
        self.AI_PROMPT_ANALYSIS = str(env_or_yaml(["VIGILANT_PROMPT_ANALYSIS"], "ai.prompts.analysis", ""))
        self.AI_PROMPT_REPORT = str(env_or_yaml(["VIGILANT_PROMPT_REPORT"], "ai.prompts.report", ""))
        self.AI_PROMPT_REPORT_SYSTEM = str(
            env_or_yaml(["VIGILANT_PROMPT_REPORT_SYSTEM"], "ai.prompts.report_system", "")
        )

        self.AI_FILTER_BACKEND = str(env_or_yaml(["VIGILANT_FILTER_BACKEND"], "ai.filter_backend", "llava")).lower()
        self.AI_SAMPLE_INTERVAL = _to_int(env_or_yaml(["VIGILANT_AI_SAMPLE_INTERVAL"], "ai.sample_interval", 5), 5)
        self.OLLAMA_URL = str(env_or_yaml(["VIGILANT_OLLAMA_URL"], "ai.ollama_url", "http://localhost:11434"))
        self.AI_FILTER_MIN_CONFIDENCE = _to_float(
            env_or_yaml(["VIGILANT_FILTER_MIN_CONFIDENCE"], "ai.filter_min_confidence", 0.60), 0.60
        )
        self.AI_EMBED_THRESHOLD = _to_float(
            env_or_yaml(["VIGILANT_EMBED_THRESHOLD"], "ai.embed_threshold", 0.30), 0.30
        )
        self.AI_USE_EMBEDDINGS = _to_bool(
            env_or_yaml(["VIGILANT_USE_EMBEDDINGS"], "ai.use_embeddings", False), False
        )
        self.AI_FILTER_MAX_TOKENS = _to_int(
            env_or_yaml(["VIGILANT_FILTER_MAX_TOKENS"], "ai.filter_max_tokens", 48), 48
        )
        self.AI_ANALYSIS_MAX_TOKENS = _to_int(
            env_or_yaml(["VIGILANT_ANALYSIS_MAX_TOKENS"], "ai.analysis_max_tokens", 256), 256
        )
        self.AI_REPORT_MAX_TOKENS = _to_int(
            env_or_yaml(["VIGILANT_REPORT_MAX_TOKENS"], "ai.report_max_tokens", 512), 512
        )
        self.AI_REPORT_MAX_ITEMS = _to_int(
            env_or_yaml(["VIGILANT_REPORT_MAX_ITEMS"], "ai.report_max_items", 50), 50
        )

        # Estrategia de extracción de frames
        self.FRAME_MODE = str(env_or_yaml(["VIGILANT_FRAME_MODE"], "frames.mode", "interval")).lower()
        self.FRAME_SCENE_THRESHOLD = _to_float(
            env_or_yaml(["VIGILANT_FRAME_SCENE_THRESHOLD"], "frames.scene_threshold", 0.20), 0.20
        )
        self.FRAME_SCALE = _to_int(env_or_yaml(["VIGILANT_FRAME_SCALE"], "frames.scale", 0), 0)

        # Motion detection settings (YOLO-only)
        self.MOTION_ENABLE = _to_bool(
            env_or_yaml(["VIGILANT_MOTION_ENABLE"], "motion.enable", False), False
        )
        self.MOTION_REQUIRE_KEYWORDS = _to_bool(
            env_or_yaml(["VIGILANT_MOTION_REQUIRE_KEYWORDS"], "motion.require_keywords", True), True
        )
        motion_keywords = env_or_yaml(["VIGILANT_MOTION_KEYWORDS"], "motion.keywords", [])
        self.MOTION_KEYWORDS = motion_keywords
        self.MOTION_MIN_DISPLACEMENT = _to_float(
            env_or_yaml(["VIGILANT_MOTION_MIN_DISPLACEMENT"], "motion.min_displacement_px", 12.0), 12.0
        )
        self.MOTION_MIN_FRAMES = _to_int(
            env_or_yaml(["VIGILANT_MOTION_MIN_FRAMES"], "motion.min_frames", 2), 2
        )

        # Metadata de escenario (opcional)
        scenario = _get_nested(self._yaml, "scenario")
        self.SCENARIO = scenario if isinstance(scenario, dict) else {}
        profile = _get_nested(self._yaml, "_profile_applied")
        self.SCENARIO_PROFILE = str(profile) if profile else ""

        # YOLO prefilter settings (optional)
        # Path al modelo YOLO - SOLO desde .env (paths no van en YAML)
        yolo_model_env = os.getenv("VIGILANT_YOLO_MODEL")
        if yolo_model_env:
            self.YOLO_MODEL = str(resolve_path(yolo_model_env, Path(yolo_model_env)))
        else:
            self.YOLO_MODEL = None
        
        self.YOLO_CONFIDENCE = _to_float(
            env_or_yaml(["VIGILANT_YOLO_CONFIDENCE"], "yolo.confidence", 0.25), 0.25
        )
        self.YOLO_IOU = _to_float(
            env_or_yaml(["VIGILANT_YOLO_IOU"], "yolo.iou", 0.45), 0.45
        )
        self.YOLO_IMG_SIZE = _to_int(
            env_or_yaml(["VIGILANT_YOLO_IMG_SIZE"], "yolo.img_size", 640), 640
        )
        self.YOLO_DEVICE = str(env_or_yaml(["VIGILANT_YOLO_DEVICE"], "yolo.device", "cpu"))
        self.YOLO_CLASSES = env_or_yaml(["VIGILANT_YOLO_CLASSES"], "yolo.classes", "")

        # Configuración de rescate rawvideo (usada cuando falla la decodificación de stream)
        self.RAW_PIX_FMT = str(env_or_yaml(["VIGILANT_RAW_PIX_FMT"], "raw.pix_fmt", "yuv420p"))
        self.RAW_RESOLUTION = str(env_or_yaml(["VIGILANT_RAW_RESOLUTION"], "raw.resolution", "1280x720"))
        self.RAW_FRAMERATE = _to_int(env_or_yaml(["VIGILANT_RAW_FRAMERATE"], "raw.framerate", 30), 30)

config = Config()
