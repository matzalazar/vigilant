# Instalación y Configuración (referencia técnica)

## Requisitos

- Python 3.8+
- `pip` y `venv`
- `ffmpeg` en PATH
- `HandBrakeCLI` en PATH
- Ollama en ejecución local (para IA)

## Instalación base

```bash
git clone https://github.com/matzalazar/vigilant.git
cd vigilant
pip install -r requirements.txt
pip install -e .
```

## Setup automatizado (opcional)

```bash
./scripts/setup.sh
```

Flags:
- `--with-yolo`
- `--download-yolo`
- `--gpu`
- `--venv=.venv`

## YOLO (opcional)

CPU-only:
```bash
pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
pip install ultralytics --no-deps
```

GPU:
```bash
pip install ultralytics
```

Pesos:
```bash
python - <<'PY'
from ultralytics import YOLO
YOLO("yolov8n.pt")
PY
```

Configurar ruta en `.env`:
```ini
VIGILANT_YOLO_MODEL="/path/to/yolov8n.pt"
```

## Modelos Ollama

```bash
ollama pull llava:13b
ollama pull mistral:latest
ollama pull nomic-embed-text:latest  # opcional (solo si se habilitan embeddings)
```

## Checks rápidos

```bash
ffmpeg -version
HandBrakeCLI --version
ollama list
vigilant --help
```

## Primera ejecución

```bash
# Verificar dependencias externas + conexión a Ollama
vigilant --check

# (Opcional) Convertir primero evidencia .mfs -> .mp4
# - Colocar archivos .mfs en VIGILANT_INPUT_DIR (por defecto: data/mfs/)
vigilant convert

# Analizar videos .mp4 en VIGILANT_OUTPUT_DIR (por defecto: data/mp4/)
vigilant analyze --prompt "Un auto oscuro"

# O analizar un único archivo:
vigilant analyze --video /ruta/al/video.mp4 --prompt "Un auto oscuro"
```
