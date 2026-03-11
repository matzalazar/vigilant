# Contribuir a Vigilant

Gracias por tu interés en contribuir a Vigilant. Este documento proporciona pautas básicas para contribuir al proyecto.

## Código de Conducta

- Usa lenguaje profesional y respetuoso
- Acepta críticas constructivas con gracia
- Enfócate en lo mejor para el proyecto

## Reportar Bugs

Antes de crear un issue:
1. Verifica que no haya sido reportado previamente
2. Asegúrate de estar usando la última versión
3. Revisa la documentación para confirmar que es un bug

Al reportar un bug, incluye:
- Descripción clara del problema
- Pasos para reproducir
- Comportamiento esperado vs actual
- Logs relevantes (desde `logs/vigilant.log`)
- Entorno (OS, Python, Vigilant version, Ollama version)

## Sugerir Mejoras

Para nuevas características:
1. Abre un issue describiendo el problema que resolvería
2. Explica por qué es importante
3. Proporciona ejemplos de uso

## Pull Requests

### Preparación

```bash
# 1. Fork y clonar
git clone https://github.com/TU_USUARIO/vigilant.git
cd vigilant

# 2. Crear rama
git checkout -b feature/mi-caracteristica

# 3. Setup entorno
pip install -e ".[dev]"
```

### Desarrollo

1. **Escribe código de calidad**:
   - Sigue PEP 8 (usa `ruff check .`)
   - Agrega type hints a funciones públicas
   - Documenta con docstrings

2. **Agrega tests**:
   ```bash
   pytest -v --cov=vigilant
   ```

3. **Actualiza documentación** si cambias funcionalidad

### Commits

Usa mensajes descriptivos con prefijos:

```bash
git commit -m "feat: agregar soporte para formato .avi"
git commit -m "fix: corregir cálculo de hash en Windows"
git commit -m "docs: actualizar guía de configuración"
```

**Prefijos:**
- `feat:` - Nueva característica
- `fix:` - Corrección de bug
- `docs:` - Cambios en documentación
- `test:` - Agregar o modificar tests
- `refactor:` - Refactorización
- `chore:` - Mantenimiento

### Enviar PR

```bash
git push origin feature/mi-caracteristica
```

En GitHub, crea el Pull Request con:
- Título descriptivo
- Descripción de cambios
- Referencia a issues relacionados (#123)

## Estilo de Código

### Python

```python
from pathlib import Path
from typing import Optional

def procesar_video(
    video_path: Path,
    output_dir: Path,
    preset: Optional[str] = None
) -> Path:
    """
    Procesa un archivo de video.
    
    Args:
        video_path: Ruta al video de entrada
        output_dir: Directorio de salida
        preset: Preset de conversión (opcional)
    
    Returns:
        Ruta del archivo procesado
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video no encontrado: {video_path}")
    
    return output_dir / f"{video_path.stem}.mp4"
```

**Principios:**
- Type hints en funciones públicas
- Docstrings en formato Google
- Nombres descriptivos

### Tests

```python
def test_calculate_sha256_archivo_valido(tmp_path):
    """El cálculo de SHA-256 debe ser correcto."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("contenido de prueba")
    
    hash_result = calculate_sha256(test_file)
    
    assert len(hash_result) == 64
    assert hash_result.islower()
```

## Setup Local Completo

```bash
# Clonar
git clone https://github.com/matzalazar/vigilant.git
cd vigilant

# Entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Instalar en modo desarrollo
pip install -e ".[dev]"

# Opcional: YOLO
pip install ".[yolo]"

# Linting
ruff check .
ruff format .
```

## Contacto

- Issues: [GitHub Issues](https://github.com/matzalazar/vigilant/issues)
- Discusiones: [GitHub Discussions](https://github.com/matzalazar/vigilant/discussions)

## Licencia

Al contribuir a Vigilant, aceptas que tus contribuciones sean licenciadas bajo GPL-3.0.

---

Gracias por contribuir a Vigilant. 
