# Configuration Reference (.env + YAML)

## Precedence

1) `config/default.yaml`
2) `config/local.yaml` (optional)
3) Environment variables (highest priority)

Scenario profiles are applied after the YAML merge and before environment variables.

## .env (Mainly Paths)

```ini
VIGILANT_INPUT_DIR="/mnt/evidence/raw"
VIGILANT_OUTPUT_DIR="/mnt/evidence/processed"
VIGILANT_YOLO_MODEL="/path/to/yolov8n.pt"  # optional
```

> [!NOTE]
> Although it is recommended to use `.env` only for paths, Vigilant also accepts environment variable overrides for logging and AI models
> (e.g., `VIGILANT_LOG_LEVEL`, `VIGILANT_OLLAMA_URL`, `VIGILANT_ANALYSIS_MODEL`).

## YAML Structure

Supported sections:
- `paths`
- `logging`
- `handbrake`
- `ai`
- `frames`
- `yolo`
- `motion`
- `raw`
- `scenario` + `profiles`

## Prompts (Templates)

```yaml
ai:
  prompts:
    filter: |
      Analyze the image and decide if it meets the criteria.
      Criteria: {prompt}
      Respond ONLY in JSON with: match (yes/no), confidence (0-100), detail (<=8 words).
    analysis: |
      Analyze the image with forensic criteria.
      Objective: {prompt}
      Describe what is relevant and why it matches.
    report: |
      Draft a professional report in English with a legal style.

      MANDATORY FORMAT (Markdown):
      Observable Facts:
      - ...
      Relevant Matches:
      - ...
      Observations:
      - ...
      Limitations:
      - ...

      Object of search: {prompt}
      Base your writing only on these records:
      {items}
    report_system: "You are a specialized legal writer."
```

> [!NOTE]
> The CLI sanitizes the "legal report (AI)". If the model does not respect the sections + bullets format, the report may be discarded.

## Scenarios (Auto-adjustment)

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

## Motion (YOLO)

```yaml
motion:
  enable: true
  require_keywords: true
  keywords: ["moving", "in motion", "en movimiento"]
  min_displacement_px: 12
  min_frames: 2
```

## Rawvideo (Rescue)

```yaml
raw:
  pix_fmt: "yuv420p"
  resolution: "1280x720"
  framerate: 30
```
