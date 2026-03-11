# Conversión de Video - Formatos Propietarios a Estándar

Este documento describe el proceso de conversión de archivos de video en formatos propietarios de CCTV (actualmente `.mfs`) a formato estándar MP4.

## Problema Resuelto

Los sistemas de vigilancia CCTV utilizan formatos propietarios que:

- No se pueden reproducir en reproductores estándar (VLC, QuickTime, Windows Media Player)
- Requieren software propietario del fabricante
- Dificultan preservación a largo plazo
- Complican compartir evidencia con peritos externos
- No son compatibles con herramientas forenses estándar

**Solución:** Convertir a MP4 estándar manteniendo integridad visual y chain of custody.

## Herramientas de Conversión

Vigilant utiliza dos herramientas en cascada:

### HandBrakeCLI (Primaria)

**Características:**
- Conversión de alta calidad
- Múltiples presets optimizados
- Amplia compatibilidad con codecs
- Salida MP4/MKV estándar

**Uso en Vigilant:**
```bash
HandBrakeCLI -i input.mfs -o output.mp4 --preset "Fast 1080p30"
```

Resultados variables según el origen y condición del archivo.

### FFmpeg (Fallback/Rescue)

**Características:**
- Mayor tolerancia a errores
- Capacidad de ignorar headers corruptos
- Extracción raw de streams

**Uso en Vigilant (remux bitexact):**
```bash
ffmpeg -y -i input.mfs -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy output.mp4
```

Resultados variables según el origen y condición del archivo.

## Proceso de Conversión Estándar

### CLI - Conversión Básica

```bash
# Convertir todos los archivos .mfs en directorio de entrada
vigilant convert

# Especificar directorios custom
vigilant convert --input-dir /evidence/raw --output-dir /evidence/processed
```

### CLI - Con Rescue Mode

```bash
# Rescue mode está habilitado por defecto: si HandBrake falla, Vigilant intenta remux y luego rescate.
vigilant convert

# (Opcional) Desactivar rescue mode (solo HandBrake)
vigilant convert --no-rescue

# Output:
# ✓ archivo_normal.mfs → archivo_normal.mp4 (HandBrake)
# ⚠ archivo_corrupto.mfs → archivo_corrupto.mp4 (ffmpeg remux) o archivo_corrupto_forced.mp4 (ffmpeg rescue)
```

### Configuración YAML

```yaml
# config/local.yaml
handbrake:
  preset: "Fast 1080p30"  # Preset de HandBrake

# Nota:
# - Si el archivo de salida ya existe, el CLI lo omite automáticamente.
# - No hay flags adicionales de conversión fuera de los que expone HandBrake.
```

## Archivos Generados

Para cada conversión exitosa se generan:

### 1. Video Convertido (`.mp4`)

```bash
output/
└── evidence_20260131.mp4  # Video en formato estándar
```

**Características:**
- Codec: H.264 por defecto (HandBrake); en rescue puede variar
- Contenedor: MP4
- Compatible con todos los reproductores estándar

### 2. Hash de Verificación (`.sha256`)

```bash
output/
└── evidence_20260131.mp4.sha256
```

**Contenido (incluye label opcional):**
```
# Converted Video
d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7  evidence_20260131.mp4
```

**Nota:** `sha256sum -c` ignora líneas que comienzan con `#`.

**Verificación:**
```bash
sha256sum -c evidence_20260131.mp4.sha256
# Output: evidence_20260131.mp4: OK
```

### 3. Metadata Forense (`.integrity.json`)

```bash
output/
└── evidence_20260131.mp4.integrity.json
```

**Estructura:**

> [!NOTE]
> `conversion.tool` refleja el pipeline real ejecutado. Valores típicos:
> - `HandBrake` (solo transcode)
> - `HandBrake+ffmpeg normalize` (transcode + normalización de metadata del contenedor)
> - `ffmpeg remux` / `ffmpeg rescue` (fallback/rescate)

```json
{
  "integrity_version": "1.0",
  "timestamp": "2026-01-31T14:23:45.123456+00:00",
  "source": {
    "path": "/evidence/raw/evidence_20260131.mfs",
    "filename": "evidence_20260131.mfs",
    "sha256": "a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0...",
    "size_bytes": 1258291200
  },
  "converted": {
    "path": "/evidence/processed/evidence_20260131.mp4",
    "filename": "evidence_20260131.mp4",  
    "sha256": "d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4...",
    "size_bytes": 987654321
  },
  "conversion": {
    "tool": "HandBrake+ffmpeg normalize",
    "preset": "Fast 1080p30",
    "command": "HandBrakeCLI -i /evidence/raw/evidence_20260131.mfs -o /evidence/processed/evidence_20260131.mp4 --preset 'Fast 1080p30' && ffmpeg -y -i /evidence/processed/evidence_20260131.mp4 -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy /evidence/processed/evidence_20260131_normalized.mp4",
    "tool_version": "HandBrakeCLI 1.6.1; ffmpeg 6.1",
    "rescue_mode": false
  }
}
```

## Logs de Conversión

### Conversión Exitosa

```
[2026-01-31 14:15:00] INFO - convirtiendo path=/evidence_20260131.mfs
[2026-01-31 14:15:30] INFO - convertido path=/evidence_20260131.mfs
[2026-01-31 14:15:35] INFO - hash original=a3f5e9c2... archivo=/evidence_20260131.mfs
[2026-01-31 14:15:35] INFO - hash convertido=d9e3f6a0... archivo=/evidence_20260131.mp4
[2026-01-31 14:15:35] INFO - integridad guardada path=/evidence_20260131.mp4.integrity.json
```

### Conversión con Rescue

```
[2026-01-31 14:20:00] INFO - convirtiendo path=/corrupted_file.mfs
[2026-01-31 14:20:10] ERROR - fallo path=/corrupted_file.mfs err=codec not supported
[2026-01-31 14:20:10] INFO - fallo path=/corrupted_file.mfs rescate=si
[2026-01-31 14:20:11] INFO - remux path=/corrupted_file.mfs
[2026-01-31 14:20:12] ERROR - remux fallo path=/corrupted_file.mfs
[2026-01-31 14:20:13] INFO - rescate path=/corrupted_file.mfs
[2026-01-31 14:20:45] INFO - rescate ok path=/corrupted_file.mfs
[2026-01-31 14:20:45] INFO - hash original=abc123... archivo=/corrupted_file.mfs
[2026-01-31 14:20:45] INFO - hash convertido=def456... archivo=/corrupted_file_forced.mp4
[2026-01-31 14:20:45] INFO - integridad guardada path=/corrupted_file_forced.mp4.integrity.json
```

## Batch Processing

### Procesamiento de Directorios Completos

```bash
# Estructura de entrada
evidence/raw/
├── footage_001.mfs
├── footage_002.mfs
├── footage_003.mfs
└── footage_004.mfs

# Ejecutar conversión batch
vigilant convert --input-dir evidence/raw --output-dir evidence/processed

# Output
evidence/processed/
├── footage_001.mp4
├── footage_001.mp4.sha256
├── footage_001.mp4.integrity.json
├── footage_002.mp4
├── footage_002.mp4.sha256
├── footage_002.mp4.integrity.json
...
```

### Procesamiento Selectivo

```bash
# Convertir todo el directorio
vigilant convert --input-dir data/mfs --output-dir data/mp4

# Convertir un único archivo
# (mover o copiar solo ese archivo a un directorio temporal y ejecutar convert)
```

**Nota:** El CLI actualmente procesa todos los archivos `.mfs` encontrados recursivamente en `--input-dir`.
Si el archivo de salida ya existe, se omite automáticamente.

## Automatización vía CLI

### Conversión Individual

> [!NOTE]
> Vigilant **solo se ejecuta vía CLI**. Para automatización, usar scripts de shell que llamen al CLI.

**Ejemplo de automatización:**

```bash
#!/bin/bash
# Procesar archivos nuevos diariamente
vigilant convert --input-dir /evidence/new --output-dir /evidence/converted
```

### Batch Conversion

```bash
# Conversión batch vía CLI
vigilant convert --input-dir /evidence/raw --output-dir /evidence/processed
```

## Verificación Post-Conversión

### Verificar Integridad

```bash
# Verificar hash
sha256sum -c evidence.mp4.sha256

# Verificar que el video es reproducible
ffprobe evidence.mp4

# Reproducir para inspección visual
vlc evidence.mp4
```

### Comparar con Original

```bash
# Duración (debe ser similar)
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 original.mfs
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 converted.mp4

# Resolución
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 original.mfs
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 converted.mp4
```

## Presets de HandBrake

### Presets Recomendados

| Preset | Resolución | FPS | Velocidad | Tamaño |
|--------|------------|-----|-----------|--------|
| `Fast 1080p30` | 1920x1080 | 30 | Rápido | Medio |
| `Fast 720p30` | 1280x720 | 30 | Muy rápido | Pequeño |
| `HQ 1080p30` | 1920x1080 | 30 | Lento | Grande |

### Configurar Preset Custom

```yaml
# config/local.yaml
handbrake:
  preset: "HQ 1080p30"  # Mayor calidad, más lento
```

### Ajustes de Calidad/Velocidad

```yaml
# Para procesamiento más rápido (menor calidad)
handbrake:
  preset: "Very Fast 720p30"

# Para máxima calidad (más lento)
handbrake:
  preset: "HQ 1080p30 Surround"
```

## Troubleshooting

Ver [10_troubleshooting.md](10_troubleshooting.md) para problemas comunes de conversión.

Para archivos que fallan incluso con rescue mode, ver [05_rescue_mode.md](05_rescue_mode.md) para técnicas avanzadas.

## Referencias

- **HandBrake:** https://handbrake.fr/docs/
- **FFmpeg:** https://ffmpeg.org/documentation.html
- **MP4 Container:** ISO/IEC 14496-14

---

**Siguiente:** [05_rescue_mode.md](05_rescue_mode.md) - Pipeline de rescate para archivos corruptos
