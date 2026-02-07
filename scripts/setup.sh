#!/usr/bin/env bash
#
# Script de instalación de Vigilant
# ----------------------------------
# Este script crea un virtualenv, instala dependencias y opcionalmente
# instala YOLO en modo solo-CPU para evitar paquetes NVIDIA/CUDA.
#
# Uso:
#   ./scripts/setup.sh
#   ./scripts/setup.sh --with-yolo
#   ./scripts/setup.sh --with-yolo --gpu
#   ./scripts/setup.sh --with-yolo --download-yolo
#   ./scripts/setup.sh --venv=.venv
#
# Notas:
# - Solo-CPU es el default para mantener instalaciones livianas.
# - Si usas --gpu, tu índice de pip puede descargar wheels habilitados para CUDA.
# - El script no sobrescribirá .env o config/local.yaml existentes.

set -euo pipefail

WITH_YOLO=false
CPU_ONLY=true
DOWNLOAD_YOLO=false
VENV_DIR=".venv"

for arg in "$@"; do
  case "$arg" in
    --with-yolo) WITH_YOLO=true ;;
    --no-yolo) WITH_YOLO=false ;;
    --gpu) CPU_ONLY=false ;;
    --cpu-only) CPU_ONLY=true ;;
    --download-yolo) DOWNLOAD_YOLO=true ;;
    --venv=*) VENV_DIR="${arg#*=}" ;;
    -h|--help)
      sed -n '1,40p' "$0"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      exit 1
      ;;
  esac
done

if ! command -v python3 >/dev/null 2>&1; then
  echo "python3 is required but not found."
  exit 1
fi

if [ ! -d "$VENV_DIR" ]; then
  echo "Creating virtualenv at $VENV_DIR"
  python3 -m venv "$VENV_DIR"
fi

# shellcheck source=/dev/null
source "$VENV_DIR/bin/activate"

echo "Upgrading pip"
pip install --upgrade pip

echo "Installing project in editable mode"
pip install -e .

if [ "$WITH_YOLO" = true ]; then
  echo "Instalando dependencias YOLO"
  if [ "$CPU_ONLY" = true ]; then
    # Forzar wheels de torch solo-CPU para evitar paquetes CUDA/NVIDIA.
    pip install --index-url https://download.pytorch.org/whl/cpu torch torchvision torchaudio
    pip install ultralytics --no-deps
  else
    # Instalación con GPU (puede descargar wheels CUDA desde índice default)
    pip install ultralytics
  fi

  if [ "$DOWNLOAD_YOLO" = true ]; then
    echo "Descargando pesos YOLO (yolov8n.pt)"
    python - <<'PY'
from ultralytics import YOLO
YOLO("yolov8n.pt")
print("Descargado yolov8n.pt (si no estaba presente).")
PY
  fi
fi

if [ ! -f ".env" ]; then
  echo "Creating .env from .env.example"
  cp .env.example .env
fi

if [ ! -f "config/local.yaml" ]; then
  if [ -f "config/local.example.yaml" ]; then
    echo "Creando config/local.yaml desde config/local.example.yaml"
    cp config/local.example.yaml config/local.yaml
  else
    echo "Creando config/local.yaml desde config/default.yaml"
    cp config/default.yaml config/local.yaml
  fi
fi

echo "Instalación completa."
echo "Próximos pasos:"
echo "  1) Editar .env (rutas) y config/local.yaml (configuración)."
echo "  2) Ejecutar: vigilant analyze --prompt \"Un auto oscuro\""
