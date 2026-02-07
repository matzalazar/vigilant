# Chain of Custody - Sistema de Integridad Forense

Este documento describe el sistema de integridad forense de Vigilant, diseñado para mantener una cadena de custodia completa y verificable de evidencia digital.

## Introducción

En investigaciones forenses y procedimientos legales, es crítico demostrar que la evidencia **no ha sido alterada** desde su captura original. Vigilant implementa un sistema automatizado de chain of custody basado en:

- **Hashes criptográficos** (SHA-256) de archivos de evidencia (origen + convertido)
- **Metadata forense** completa en formato JSON
- **Trazabilidad** de todas las transformaciones
- **Verificación independiente** con herramientas estándar

## Características del Sistema

### 1. Cálculo Automático de Hashes SHA-256

Vigilant calcula automáticamente hashes SHA-256 de:

- **Archivo origen** (`.mfs` propietario)
- **Archivo convertido** (`.mp4` estándar)
- Genera un archivo **`.sha256`** asociado al `.mp4` convertido (contiene el hash del `.mp4`)

> [!NOTE]
> Los reportes de análisis (`.md`) y screenshots (`.jpg`) **no** se hashean automáticamente.
> Si se requiere trazabilidad completa de esos artefactos, se recomienda calcular hashes adicionales manualmente.

**Características técnicas:**
- Algoritmo: SHA-256 (NIST FIPS 180-4)
- Longitud: 256 bits (64 caracteres hexadecimales)
- Chunk size: 8KB (eficiencia en memoria)
- Rendimiento: ~100MB/s en CPU moderna

**Implementación (fragmento interno, no API pública):**

```python
def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calcula SHA-256 de un archivo de forma eficiente.
    
    Uses streaming read (8KB chunks) to minimize memory footprint.
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()
```

### 2. Archivos de Integridad Generados

#### Archivo `.sha256` (Formato Estándar)

Formato compatible con `sha256sum` de GNU/Linux. Vigilant agrega una línea
de comentario opcional (label) antes del hash:

```text
# Converted Video
a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2  video.mp4
```

**Nota:** `sha256sum -c` ignora líneas que comienzan con `#`.

**Verificación con herramientas estándar:**

```bash
# Linux/macOS
sha256sum -c video.mp4.sha256

# Windows PowerShell (ignorar líneas de comentario)
$expected = Get-Content video.mp4.sha256 |
  Where-Object { $_ -notmatch '^#' } |
  ForEach-Object { $_.Split(" ")[0] } |
  Select-Object -First 1
$actual = (Get-FileHash video.mp4 -Algorithm SHA256).Hash.ToLower()
if ($expected -eq $actual) { "OK" } else { "FAILED" }
```

#### Archivo `.integrity.json` (Metadata Forense Completa)

Estructura JSON con información detallada:

```json
{
  "integrity_version": "1.0",
  "timestamp": "2026-01-31T14:23:45.123456+00:00",
  "source": {
    "path": "/evidence/original_cctv_footage.mfs",
    "filename": "original_cctv_footage.mfs",
    "sha256": "a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2",
    "size_bytes": 1258291200
  },
  "converted": {
    "path": "/processed/original_cctv_footage.mp4",
    "filename": "original_cctv_footage.mp4",
    "sha256": "d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7",
    "size_bytes": 987654321
  },
  "conversion": {
    "tool": "HandBrake+ffmpeg normalize",
    "preset": "Fast 1080p30",
    "command": "HandBrakeCLI -i /evidence/original_cctv_footage.mfs -o /processed/original_cctv_footage.mp4 --preset 'Fast 1080p30' && ffmpeg -y -i /processed/original_cctv_footage.mp4 -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy /processed/original_cctv_footage_normalized.mp4",
    "tool_version": "HandBrakeCLI 1.6.1; ffmpeg 6.1",
    "rescue_mode": false
  }
}
```

**Campos:**
- `integrity_version`: Versión del esquema de metadata
- `timestamp`: Timestamp UTC ISO 8601 del momento de conversión
- `source`: Información del archivo original
  - `path`: Ruta del archivo (según se ejecutó; puede ser absoluta o relativa)
  - `filename`: Nombre del archivo
  - `sha256`: Hash completo del archivo original
  - `size_bytes`: Tamaño en bytes
- `converted`: Información del archivo convertido (estructura igual)
- `conversion`: Detalles de la conversión
  - `tool`: Herramienta utilizada (HandBrake, FFmpeg)
  - `preset`: Preset de conversión aplicado
  - `command`: Comando ejecutado (incluye normalización de metadata si aplica)
  - `tool_version`: Versión(es) de herramienta(s) usada(s)
  - `rescue_mode`: `true` si se usó rescue mode

### 3. Inclusión en Reportes de Análisis

Cuando se genera un reporte de análisis IA, el hash SHA-256 se incluye automáticamente:

```markdown
# Reporte de Análisis - 2026-01-31 14:30:00

## Video Analizado

- **Archivo**: `evidence_20260131.mp4`
- **SHA-256**: `d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7`
- **Duración**: 00:06:00
- **Frames analizados**: 72
- **Criterio**: person with red backpack

...
```

Esto permite correlacionar el reporte con el archivo exacto analizado.

## Flujo de Trabajo Forense

### Paso 1: Recepción de Evidencia

```bash
$ ls evidence/
incident_2026_01_31.mfs

$ sha256sum evidence/incident_2026_01_31.mfs
a3f5e9c2...  evidence/incident_2026_01_31.mfs
```

**Documentar:** Registrar hash del archivo recibido en log de evidencia.

### Paso 2: Conversión con Chain of Custody

```bash
$ vigilant convert --input-dir evidence/ --output-dir processed/

[2026-01-31 14:15:00] INFO - Procesando: incident_2026_01_31.mfs
[2026-01-31 14:15:05] INFO - Hash original: a3f5e9c2... archivo=incident_2026_01_31.mfs
[2026-01-31 14:15:30] INFO - Conversión exitosa con HandBrake
[2026-01-31 14:15:35] INFO - Hash convertido: d9e3f6a0... archivo=incident_2026_01_31.mp4
[2026-01-31 14:15:35] INFO - Metadata guardada: incident_2026_01_31.mp4.integrity.json
```

### Paso 3: Verificación de Archivos Generados

```bash
$ ls processed/
incident_2026_01_31.mp4
incident_2026_01_31.mp4.sha256
incident_2026_01_31.mp4.integrity.json

$ cat processed/incident_2026_01_31.mp4.sha256
# Converted Video
d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2...  incident_2026_01_31.mp4

$ sha256sum -c processed/incident_2026_01_31.mp4.sha256
incident_2026_01_31.mp4: OK
```

### Paso 4: Transferencia Segura

```bash
# Antes de transferir
$ sha256sum processed/incident_2026_01_31.mp4 > transfer_hash.txt

# Transferir archivo + hash
$ scp processed/incident_2026_01_31.mp4 forensic-server:/evidence/
$ scp processed/incident_2026_01_31.mp4.integrity.json forensic-server:/evidence/
$ scp transfer_hash.txt forensic-server:/evidence/

# En servidor destino: verificar
$ ssh forensic-server
$ cd /evidence
$ sha256sum incident_2026_01_31.mp4
d9e3f6a0...  incident_2026_01_31.mp4

$ # Comparar con transfer_hash.txt - deben coincidir
```

### Paso 5: Documentación Legal

**Extracto de informe pericial:**

> *"Se recibió archivo de video en formato propietario `.mfs` con hash SHA-256 `a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2`.*
>
> *El archivo fue convertido a formato estándar MP4 utilizando la herramienta Vigilant v0.2.0 con backend HandBrakeCLI, preset 'Fast 1080p30', sin alteración del contenido visual.*
>
> *El archivo resultante `incident_2026_01_31.mp4` tiene hash SHA-256 `d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7`.*
>
> *La integridad del archivo fue verificada el 2026-01-31 a las 15:00 UTC mediante cálculo independiente de hash SHA-256, con resultado positivo."*

## Alineación con Estándares

Vigilant implementa **SHA-256** y registra metadata de conversión. Esto **ayuda**
a alinearse con prácticas forenses, pero **no constituye certificación** ni
garantiza cumplimiento normativo por sí solo (depende de procesos y controles
de la organización).

| Referencia | Cobertura real | Notas |
|------------|----------------|-------|
| **NIST FIPS 180-4** | Implementado | Uso de SHA-256 para hashes |
| **RFC 6234** | Implementado | Implementación estándar SHA-2 |
| **ISO 27037 / guías forenses** | Parcial | Aporta hashes + metadata, pero no reemplaza procedimientos |

**Referencias:**
- [NIST FIPS 180-4](https://csrc.nist.gov/publications/detail/fips/180/4/final)
- [ISO 27037:2012](https://www.iso.org/standard/44381.html)
- [NIST Computer Forensics Tool Testing](https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-tool-testing-program-cftt)
- [RFC 6234 - SHA-2](https://www.rfc-editor.org/rfc/rfc6234)

## Uso (CLI)

Los archivos de integridad se generan automáticamente al usar el CLI:

```bash
vigilant convert --input-dir data/mfs --output-dir data/mp4
```

Los archivos `.integrity.json` y `.sha256` se crean en el mismo directorio que el archivo MP4 resultante.

### Verificación de Integridad

```bash
# Verificar hash con herramienta estándar
sha256sum -c evidence.mp4.sha256
```

## Mejores Prácticas

### 1. Preservar Archivos Originales

**Mal:**
```bash
vigilant convert && rm -rf evidence/
```

**Bien:**
```bash
vigilant convert
# Archivos originales se mantienen intactos
```

### 2. Documentar Hashes en Log de Casos

Ejemplo de entrada de log:

```
=== Evidence Log Entry #42 ===
Date: 2026-01-31 14:00 UTC
Case ID: INV-2026-0131
Operator: J. Smith

Original File:
  Name: incident_2026_01_31.mfs
  Size: 1,258,291,200 bytes
  SHA-256: a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2

Conversion:
  Tool: Vigilant v0.2.0 (HandBrake backend)
  Timestamp: 2026-01-31 14:15:35 UTC
  
Converted File:
  Name: incident_2026_01_31.mp4
  Size: 987,654,321 bytes
  SHA-256: d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7

Verification: PASSED (2026-01-31 15:00 UTC)
```

### 3. Verificar Antes de Archivar

```bash
# Antes de mover a almacenamiento a largo plazo
cd processed/
sha256sum -c *.sha256

# Debe mostrar:
# incident_2026_01_31.mp4: OK
```

### 4. Almacenar Configuración

Guardar snapshot de configuración junto con metadata:

```bash
cp config/local.yaml processed/incident_2026_01_31_config_snapshot.yaml
```

### 5. Mantener Cadena de Custodia

Ejemplo de log de custodia completo:

```
2026-01-31 08:00 UTC - Evidence received from field (hash: a3f5e9c2...)
2026-01-31 14:15 UTC - Converted to MP4 (hash: d9e3f6a0...)
2026-01-31 14:30 UTC - Transferred to secure storage
2026-01-31 15:00 UTC - Integrity verified (SHA-256 match)
2026-02-01 09:00 UTC - Analyzed with AI assistant
2026-02-01 10:00 UTC - Re-verified integrity (SHA-256 match)
2026-02-01 14:00 UTC - Report submitted to case file
```

## Impacto en Performance

| File Size | Hash Calculation Time | Memory Usage |
|-----------|----------------------|--------------|
| 100 MB | ~1 second | 8 KB |
| 1 GB | ~10 seconds | 8 KB |
| 10 GB | ~100 seconds (~1.5 min) | 8 KB |

**Características:**
- Overhead: ~1-2 segundos por cada 100MB
- Throughput: ~100MB/s en CPU moderno (Intel i5 o superior)
- Memory footprint: Constante 8KB (streaming, no carga archivo completo)

## Troubleshooting

### Error: Permission Denied

```
WARNING - fallo calculo hash path=/video.mp4 err=Permission denied
```

**Solución:**
```bash
# Verificar permisos
ls -l /video.mp4

# Dar permisos de lectura
chmod 644 /video.mp4
```

### Error: Hash Mismatch Después de Transferencia

```bash
$ sha256sum transferred_file.mp4
xyz789...  transferred_file.mp4

# ✗ No coincide con hash documentado
```

**Causas comunes:**
- Corrupción durante transferencia de red
- Disk I/O error
- Archivo modificado inadvertidamente

**Solución:**
```bash
# Re-transferir el archivo
# Usar verificación automática en scp/rsync:
rsync -avz --checksum source.mp4 destination/
```

### Archivo Bloqueado por Otro Proceso

```
ERROR - Cannot calculate hash: file is locked
```

**Solución:**
```bash
# Linux: identificar proceso
lsof /path/to/file.mp4

# Cerrar programa que tiene el archivo abierto
```

## Conclusión

El sistema de chain of custody de Vigilant proporciona:

- **Automatización** de cálculo de hashes (origen + convertido)
- **Formato estándar** compatible con herramientas forenses
- **Metadata rica** para auditorías
- **Verificación independiente** sin dependencia de Vigilant
- **Alineación parcial** con estándares y buenas prácticas (NIST, ISO)

Esto **no constituye certificación** ni garantiza por sí solo validez legal (depende de procedimientos, controles y jurisdicción), pero **ayuda a sustentar** integridad y trazabilidad de los artefactos generados y su verificación por terceros.
