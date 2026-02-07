"""
Tests para vigilant/core/config.py
"""
import os
from pathlib import Path
from unittest.mock import patch, mock_open

import pytest
import yaml

from vigilant.core.config import (
    _deep_merge,
    _apply_scenario_config,
    _to_bool,
    _to_int,
    _to_float,
    Config,
)


class TestDeepMerge:
    """Tests para la función _deep_merge."""

    def test_deep_merge_basic(self):
        """Test de merge básico de diccionarios."""
        base = {"a": 1, "b": {"c": 2}}
        override = {"b": {"d": 3}, "e": 4}
        result = _deep_merge(base, override)
        
        assert result["a"] == 1
        assert result["b"]["c"] == 2
        assert result["b"]["d"] == 3
        assert result["e"] == 4

    def test_deep_merge_override(self):
        """Test de override de valores existentes."""
        base = {"a": 1, "b": 2}
        override = {"b": 3}
        result = _deep_merge(base, override)
        
        assert result["a"] == 1
        assert result["b"] == 3

    def test_deep_merge_empty_override(self):
        """Test de merge con override vacío."""
        base = {"a": 1}
        override = {}
        result = _deep_merge(base, override)
        
        assert result == {"a": 1}


class TestApplyScenarioConfig:
    """Tests para la función _apply_scenario_config."""

    def test_apply_scenario_config_match(self):
        """Test de aplicación de perfil coincidente."""
        data = {
            "scenario": {"camera": "fixed", "lighting": "night"},
            "profiles": [
                {
                    "name": "test_profile",
                    "match": {"camera": "fixed", "lighting": "night"},
                    "overrides": {"frames": {"mode": "scene"}}
                }
            ],
            "frames": {"mode": "interval"}
        }
        
        result = _apply_scenario_config(data)
        assert result["frames"]["mode"] == "scene"

    def test_apply_scenario_config_no_match(self):
        """Test sin perfil coincidente."""
        data = {
            "scenario": {"camera": "mobile"},
            "profiles": [
                {
                    "name": "test_profile",
                    "match": {"camera": "fixed"},
                    "overrides": {"frames": {"mode": "scene"}}
                }
            ],
            "frames": {"mode": "interval"}
        }
        
        result = _apply_scenario_config(data)
        assert result["frames"]["mode"] == "interval"


class TestTypeConversion:
    """Tests para funciones de conversión de tipos."""

    def test_to_bool_true_values(self):
        """Test de conversión a bool con valores verdaderos."""
        assert _to_bool("true") is True
        assert _to_bool("TRUE") is True
        assert _to_bool("1") is True
        assert _to_bool(True) is True
        assert _to_bool(1) is True

    def test_to_bool_false_values(self):
        """Test de conversión a bool con valores falsos."""
        assert _to_bool("false") is False
        assert _to_bool("FALSE") is False
        assert _to_bool("0") is False
        assert _to_bool(False) is False
        assert _to_bool(0) is False

    def test_to_bool_default(self):
        """Test de conversión a bool con valor por defecto."""
        assert _to_bool(None, default=True) is True
        assert _to_bool("invalid", default=False) is False

    def test_to_int_valid(self):
        """Test de conversión a int válida."""
        assert _to_int("123", 0) == 123
        assert _to_int(456, 0) == 456

    def test_to_int_invalid(self):
        """Test de conversión a int inválida usa default."""
        assert _to_int("not_a_number", 999) == 999
        assert _to_int(None, 42) == 42

    def test_to_float_valid(self):
        """Test de conversión a float válida."""
        assert _to_float("1.23", 0.0) == 1.23
        assert _to_float(4.56, 0.0) == 4.56

    def test_to_float_invalid(self):
        """Test de conversión a float inválida usa default."""
        assert _to_float("not_a_number", 9.99) == 9.99
        assert _to_float(None, 4.2) == 4.2


class TestConfig:
    """Tests para la clase Config."""

    def test_config_initialization(self):
        """Test de inicialización básica de Config."""
        # Este test verifica que la configuración se pueda instanciar
        # sin lanzar excepciones
        config = Config()
        
        assert config.BASE_DIR.exists()
        assert config.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]

    @patch.dict(os.environ, {"VIGILANT_LOG_LEVEL": "DEBUG"})
    def test_config_env_override(self):
        """Test de override de configuración con variables de entorno."""
        config = Config()
        assert config.LOG_LEVEL == "DEBUG"

    def test_config_handbrake_preset(self):
        """Test de configuración de preset de HandBrake."""
        config = Config()
        assert isinstance(config.HANDBRAKE_PRESET, str)
        assert len(config.HANDBRAKE_PRESET) > 0

    def test_config_paths_resolution(self):
        """Test de resolución de paths."""
        config = Config()
        
        # Los paths deben ser Path objects
        assert isinstance(config.DATA_DIR, Path)
        assert isinstance(config.LOGS_DIR, Path)
        assert isinstance(config.INPUT_PDF_DIR, Path)
        assert isinstance(config.OUTPUT_JSON_DIR, Path)

    def test_config_ai_settings(self):
        """Test de configuración de IA."""
        config = Config()
        
        assert isinstance(config.OLLAMA_URL, str)
        assert config.OLLAMA_URL.startswith("http")
        assert isinstance(config.AI_MODEL, str)
        assert config.AI_SAMPLE_INTERVAL > 0

    def test_config_frame_extraction(self):
        """Test de configuración de extracción de frames."""
        config = Config()
        
        assert config.FRAME_MODE in ["interval", "scene", "interval+scene"]
        assert config.FRAME_SCENE_THRESHOLD >= 0.0
        assert config.FRAME_SCENE_THRESHOLD <= 1.0

    def test_config_yolo_settings(self):
        """Test de configuración de YOLO."""
        config = Config()
        
        assert isinstance(config.YOLO_CONFIDENCE, float)
        assert 0.0 <= config.YOLO_CONFIDENCE <= 1.0
        assert config.YOLO_DEVICE in ["cpu", "0", "cuda"]
