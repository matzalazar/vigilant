# Referencia de Configuración (.env + YAML)

## Precedencia

1) `config/default.yaml`
2) `config/local.yaml` (opcional)
3) Variables de entorno (máxima prioridad)

Los perfiles de escenario se aplican después del merge YAML y antes de env.

## .env (principalmente rutas)

```ini
VIGILANT_INPUT_DIR="/mnt/evidence/raw"
VIGILANT_OUTPUT_DIR="/mnt/evidence/processed"
VIGILANT_YOLO_MODEL="/path/to/yolov8n.pt"  # opcional
```

> [!NOTE]
> Aunque se recomienda usar `.env` solo para rutas, Vigilant también acepta overrides por env para logging y modelos IA
> (ej: `VIGILANT_LOG_LEVEL`, `VIGILANT_OLLAMA_URL`, `VIGILANT_ANALYSIS_MODEL`).

## Estructura YAML

Secciones soportadas:
- `paths`
- `logging`
- `handbrake`
- `ai`
- `frames`
- `yolo`
- `motion`
- `raw`
- `scenario` + `profiles`

## Prompts (plantillas)

```yaml
ai:
  prompts:
    filter: |
      Analiza la imagen y decide si cumple el criterio.
      Criterio: {prompt}
      Responde SOLO en JSON con: match (yes/no), confidence (0-100), detail (<=8 palabras).
    analysis: |
      Analiza la imagen con criterio forense.
      Objetivo: {prompt}
      Describe lo relevante y por qué coincide.
    report: |
      Redacta un informe profesional en español con estilo juridico.

      FORMATO OBLIGATORIO (Markdown):
      Hechos Observables:
      - ...
      Coincidencias relevantes:
      - ...
      Observaciones:
      - ...
      Limitaciones:
      - ...

      Objeto de busqueda: {prompt}
      Base tu redaccion solo en estos registros:
      {items}
    report_system: "Eres un redactor juridico especializado."
```

> [!NOTE]
> El CLI sanitiza el "Informe juridico (IA)". Si el modelo no respeta el formato de secciones + bullets, el informe puede descartarse.

## Escenarios (auto-ajuste)

```yaml
scenario:
  camera: "fixed"
  lighting: "night"
  motion: true

profiles:
  - name: "fixed_night_motion"
    match:
      camera: "fixed"
      lighting: "night"
      motion: true
    overrides:
      frames:
        mode: "interval+scene"
        scene_threshold: 0.02
      ai:
        sample_interval: 8
        filter_backend: "yolo"
```

## Frames

```yaml
frames:
  mode: "interval+scene"   # interval | scene | interval+scene
  scene_threshold: 0.05
  scale: 480
```

## YOLO

```yaml
yolo:
  confidence: 0.25
  iou: 0.45
  img_size: 640
  device: "cpu"
  classes: ["person", "car"]
```

## Movimiento (YOLO)

```yaml
motion:
  enable: true
  require_keywords: true
  keywords: ["moving", "in motion", "en movimiento"]
  min_displacement_px: 12
  min_frames: 2
```

## Rawvideo (rescate)

```yaml
raw:
  pix_fmt: "yuv420p"
  resolution: "1280x720"
  framerate: 30
```
