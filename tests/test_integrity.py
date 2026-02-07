"""
Tests para el módulo de integridad forense.
"""

import pytest
from pathlib import Path
import tempfile
import json
from vigilant.core.integrity import (
    calculate_sha256,
    generate_integrity_report,
    save_sha256_file,
    generate_conversion_metadata,
    save_metadata_json,
    verify_integrity
)


def test_calculate_sha256():
    """Test cálculo de SHA-256 de archivo."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = Path(f.name)
        f.write(b"test content for hashing")
    
    try:
        hash_value = calculate_sha256(test_file)
        
        # Verificar formato
        assert len(hash_value) == 64  # SHA-256 es 64 caracteres hex
        assert all(c in '0123456789abcdef' for c in hash_value)
        
        # Verificar que el hash es determinístico
        hash_value2 = calculate_sha256(test_file)
        assert hash_value == hash_value2
        
    finally:
        test_file.unlink()


def test_calculate_sha256_file_not_found():
    """Test que falla si archivo no existe."""
    non_existent = Path("/tmp/nonexistent_file_xyz.tmp")
    
    with pytest.raises(FileNotFoundError):
        calculate_sha256(non_existent)


def test_generate_integrity_report():
    """Test generación de reporte con múltiples archivos."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f1, \
         tempfile.NamedTemporaryFile(mode='wb', delete=False) as f2:
        
        file1 = Path(f1.name)
        file2 = Path(f2.name)
        
        f1.write(b"content 1")
        f2.write(b"content 2")
    
    try:
        files = {"original": file1, "converted": file2}
        report = generate_integrity_report(files)
        
        assert "original" in report
        assert "converted" in report
        assert len(report["original"]) == 64
        assert len(report["converted"]) == 64
        assert report["original"] != report["converted"]
        
    finally:
        file1.unlink()
        file2.unlink()


def test_save_sha256_file():
    """Test guardado de archivo .sha256."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mp4') as f:
        test_file = Path(f.name)
        f.write(b"video content")
    
    try:
        test_hash = "a" * 64
        sha256_file = save_sha256_file(test_file, test_hash, label="Test Video")
        
        assert sha256_file.exists()
        assert sha256_file.name == test_file.name + '.sha256'
        
        content = sha256_file.read_text()
        assert test_hash in content
        assert test_file.name in content
        assert "Test Video" in content
        
        sha256_file.unlink()
        
    finally:
        test_file.unlink()


def test_generate_conversion_metadata():
    """Test generación de metadata de conversión."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mfs') as f1, \
         tempfile.NamedTemporaryFile(mode='wb', delete=False, suffix='.mp4') as f2:
        
        source = Path(f1.name)
        converted = Path(f2.name)
        
        f1.write(b"original")
        f2.write(b"converted")
    
    try:
        metadata = generate_conversion_metadata(
            source_path=source,
            source_hash="a" * 64,
            converted_path=converted,
            converted_hash="b" * 64,
            conversion_tool="HandBrake",
            preset="Fast 1080p30",
            command="HandBrakeCLI -i input -o output --preset=Fast 1080p30",
            tool_version="HandBrakeCLI 1.6.1",
            rescue_mode=False,
        )
        
        assert metadata["integrity_version"] == "1.0"
        assert "timestamp" in metadata
        assert metadata["source"]["sha256"] == "a" * 64
        assert metadata["converted"]["sha256"] == "b" * 64
        assert metadata["conversion"]["tool"] == "HandBrake"
        assert metadata["conversion"]["preset"] == "Fast 1080p30"
        assert metadata["conversion"]["command"].startswith("HandBrakeCLI")
        assert metadata["conversion"]["tool_version"] == "HandBrakeCLI 1.6.1"
        assert metadata["conversion"]["rescue_mode"] is False
        assert metadata["source"]["size_bytes"] > 0
        
    finally:
        source.unlink()
        converted.unlink()


def test_save_metadata_json():
    """Test guardado de metadata en JSON."""
    metadata = {
        "test_key": "test_value",
        "nested": {"key": "value"}
    }
    
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
        output_path = Path(f.name)
    
    try:
        saved_path = save_metadata_json(metadata, output_path)
        
        assert saved_path.exists()
        
        with open(saved_path, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == metadata
        
    finally:
        output_path.unlink()


def test_verify_integrity():
    """Test verificación de integridad."""
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_file = Path(f.name)
        f.write(b"content for verification")
    
    try:
        # Calcular hash correcto
        correct_hash = calculate_sha256(test_file)
        
        # Verificar con hash correcto
        assert verify_integrity(test_file, correct_hash) is True
        
        # Verificar con hash incorrecto
        wrong_hash = "z" * 64
        assert verify_integrity(test_file, wrong_hash) is False
        
        # Verificar case insensitive
        assert verify_integrity(test_file, correct_hash.upper()) is True
        
    finally:
        test_file.unlink()


def test_hash_consistency_on_same_content():
    """Test que contenido idéntico produce mismo hash."""
    content = b"consistent content for testing"
    
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f1, \
         tempfile.NamedTemporaryFile(mode='wb', delete=False) as f2:
        
        file1 = Path(f1.name)
        file2 = Path(f2.name)
        
        f1.write(content)
        f2.write(content)
    
    try:
        hash1 = calculate_sha256(file1)
        hash2 = calculate_sha256(file2)
        
        assert hash1 == hash2
        
    finally:
        file1.unlink()
        file2.unlink()
