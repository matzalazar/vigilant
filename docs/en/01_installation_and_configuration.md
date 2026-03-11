# Installation and Configuration (Technical Reference)

## Requirements

- Python 3.8+
- `pip` and `venv`
- `ffmpeg` in PATH
- `HandBrakeCLI` in PATH
- Ollama running locally (for AI)

## Base Installation

```bash
git clone https://github.com/matzalazar/vigilant.git
cd vigilant
pip install -r requirements.txt
pip install -e .
```

## Automated Setup (Optional)

```bash
./scripts/setup.sh
```

Flags:
- `--with-yolo`
- `--download-yolo`
- `--gpu`
- `--venv=.venv`

## YOLO (Optional)

CPU-only:
```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
pip install ultralytics --no-deps
```

GPU:
```bash
pip install ultralytics
```

Weights:
```bash
python - <<'PY'
from ultralytics import YOLO
YOLO("yolov8n.pt")
PY
```

Configure path in `.env`:
```ini
VIGILANT_YOLO_MODEL="/path/to/yolov8n.pt"
```

## Ollama Models

```bash
ollama pull llava:13b
ollama pull mistral:latest
ollama pull nomic-embed-text:latest  # optional (only if embeddings are enabled)
```

## Quick Checks

```bash
ffmpeg -version
HandBrakeCLI --version
ollama list
vigilant --help
```

## First Run

```bash
# Verify external dependencies + connection to Ollama
vigilant --check

# (Optional) Convert .mfs -> .mp4 evidence first
# - Place .mfs files in VIGILANT_INPUT_DIR (default: data/mfs/)
vigilant convert

# Analyze .mp4 videos in VIGILANT_OUTPUT_DIR (default: data/mp4/)
vigilant analyze --prompt "A dark car"

# Or analyze a single file:
vigilant analyze --video /path/to/video.mp4 --prompt "A dark car"
```
