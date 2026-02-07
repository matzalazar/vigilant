# Imagen base con Python 3.10
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Actualizar e instalar dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.10 \
    python3-pip \
    python3-venv \
    ffmpeg \
    handbrake-cli \
    bash \
    curl \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos de configuración primero (para aprovechar cache)
COPY requirements.txt pyproject.toml ./
COPY README.md README_EN.md ./

# Instalar dependencias de Python
RUN pip3 install --no-cache-dir -r requirements.txt

# Copiar el código del proyecto
COPY vigilant ./vigilant
COPY config ./config
COPY tests ./tests
COPY scripts ./scripts

# Instalar el proyecto en modo editable
RUN pip3 install --no-cache-dir -e .

# Crear directorios de datos
RUN mkdir -p data/mfs data/mp4 data/pdf data/json data/tmp logs

# Copiar archivo .env.example
COPY .env.example .env.example

# Variable de entorno para PYTHONPATH
ENV PYTHONPATH=/app

# Punto de entrada para el CLI
ENTRYPOINT ["vigilant"]

# Comando por defecto: mostrar ayuda
CMD ["--help"]
