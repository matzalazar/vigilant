# Deployment en Producción

Guía para desplegar Vigilant en entornos de producción con Docker.

## Requisitos de Hardware

### Mínimo (Solo Conversión)
- CPU: 2 cores
- RAM: 4GB
- Disco: 50GB SSD
- Red: 100Mbps

### Recomendado (Con Análisis IA)
- CPU: 8+ cores (o GPU con CUDA/ROCm)
- RAM: 16GB (32GB si análisis intensivo)
- Disco: 500GB+ SSD NVMe
- Red: 1Gbps

### Óptimo (Alto Volumen)
- CPU: 16+ cores o GPU dedicada
- RAM: 64GB
- Disco: 2TB+ NVMe RAID
- Red: 10Gbps

## Stack de Producción

```
┌─────────────────────────────────────┐
│          Docker Compose Stack       │
│  ┌────────────┐  ┌───────────────┐  │
│  │  Vigilant  │  │    Ollama     │  │
│  │   (app)    │←→│  (AI engine)  │  │
│  └────────────┘  └───────────────┘  │
│         │                 │         │
│         ├─────────────────┤         │
│  ┌──────┴─────────────────┴──────┐  │
│  │      Shared Volumes (datos)   │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

> [!NOTE]
> Vigilant es **CLI-only** y no expone un servicio HTTP propio. Si quieres controlar acceso de red, el punto típico a proteger/exponer es **Ollama** (puerto 11434) o la red Docker interna; un reverse proxy (Nginx/Caddy) sería un componente **externo** y opcional, no parte del proyecto.

## Deployment con Docker Compose

### 1. Preparación del Entorno

```bash
# Clonar repositorio en servidor
git clone https://github.com/matzalazar/vigilant.git /opt/vigilant
cd /opt/vigilant

# Crear directorios de datos
mkdir -p data/{mfs,mp4,pdf,json,tmp,reports/md,reports/imgs}
mkdir -p logs

# Configurar permisos
sudo chown -R $USER:$USER data/ logs/
```

### 2. Configuración

**Variables de entorno (Docker Compose):**

> [!NOTE]
> En el `docker-compose.yml` de este repo estas variables ya están definidas en `services.vigilant.environment`.
> El archivo `.env` (python-dotenv) se usa principalmente para ejecución **local** y no se monta automáticamente dentro del contenedor.
```ini
# Rutas dentro del contenedor (no modificar sin cambiar volumes)
VIGILANT_INPUT_DIR=/data/mfs
VIGILANT_OUTPUT_DIR=/data/mp4
VIGILANT_INPUT_PDF_DIR=/data/pdf
VIGILANT_OUTPUT_JSON_DIR=/data/json
VIGILANT_DATA_DIR=/app/data

# Ollama (servicio en Docker)
VIGILANT_OLLAMA_URL=http://ollama:11434

# Logging
VIGILANT_LOG_LEVEL=INFO

# YOLO (si se usa)
# VIGILANT_YOLO_MODEL=/app/models/yolov8n.pt
```

**Archivo `config/local.yaml`:**
```yaml
# Configuración optimizada para producción
logging:
  level: "INFO"

ai:
  ollama_url: "http://ollama:11434"
  
  # Modelos
  filter_backend: "yolo"  # Más rápido que llava para prefiltro
  filter_model: "llava:13b"
  analysis_model: "llava:13b"
  report_model: "mistral:latest"
  
  # Performance
  sample_interval: 5
  filter_min_confidence: 0.65
  
frames:
  mode: "interval+scene"
  scene_threshold: 0.05
  scale: 480  # Balance velocidad/calidad

yolo:
  confidence: 0.30
  iou: 0.45
  device: "cpu"  # Cambiar a "0" si GPU disponible

# Perfiles optimizados
scenario:
  camera: "fixed"
  lighting: "mixed"
  motion: true

profiles:
  - name: "produccion_estandar"
    match:
      camera: "fixed"
      lighting: "mixed"
      motion: true
    overrides:
      ai:
        sample_interval: 5
        filter_backend: "yolo"
      frames:
        mode: "interval+scene"
        scale: 480
```

### 3. Docker Compose (base)

El repositorio incluye `docker-compose.yml` como base. Para producción puedes aplicar
overrides (límites, logging, volúmenes read-only) sobre este archivo.

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  # Servicio Ollama (motor de IA)
  ollama:
    image: ollama/ollama:latest
    container_name: vigilant-ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    restart: unless-stopped
    healthcheck:
      test: [ "CMD", "curl", "-f", "http://localhost:11434/api/tags" ]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    networks:
      - vigilant-network

  # Servicio Vigilant (aplicación principal)
  vigilant:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: vigilant-app
    environment:
      # Configuración de Ollama
      - VIGILANT_OLLAMA_URL=http://ollama:11434
      # Nivel de logging
      - VIGILANT_LOG_LEVEL=INFO
      # Directorios de datos (dentro del contenedor)
      - VIGILANT_INPUT_DIR=/data/mfs
      - VIGILANT_OUTPUT_DIR=/data/mp4
      - VIGILANT_INPUT_PDF_DIR=/data/pdf
      - VIGILANT_OUTPUT_JSON_DIR=/data/json
      - VIGILANT_DATA_DIR=/app/data
    volumes:
      # Montaje de directorios de datos host -> contenedor
      - ./data/mfs:/data/mfs
      - ./data/mp4:/data/mp4
      - ./data/pdf:/data/pdf
      - ./data/json:/data/json
      # Reportes y temporales (análisis)
      - ./data/tmp:/app/data/tmp
      - ./data/reports:/app/data/reports
      # Montaje de logs
      - ./logs:/app/logs
      # Montaje de config para overrides locales
      - ./config/local.yaml:/app/config/local.yaml:ro
    depends_on:
      ollama:
        condition: service_healthy
    networks:
      - vigilant-network
    # El contenedor se mantiene vivo para ejecutar comandos
    entrypoint: [ "tail", "-f", "/dev/null" ]
    restart: unless-stopped

volumes:
  # Volumen persistente para modelos de Ollama
  ollama_data:
    driver: local

networks:
  vigilant-network:
    driver: bridge
```

### 4. Inicialización

```bash
# Construir imágenes
docker compose -f docker-compose.yml build

# Iniciar servicios
docker compose -f docker-compose.yml up -d

# Verificar estado
docker compose -f docker-compose.yml ps

# Ver logs
# - Ollama: stdout/stderr via Docker logs
# - Vigilant: archivo en host (logs/vigilant.log)
docker compose -f docker-compose.yml logs -f ollama
tail -f logs/vigilant.log
```

### 5. Descargar Modelos de IA

```bash
docker exec vigilant-ollama ollama pull llava:13b
docker exec vigilant-ollama ollama pull mistral:latest
docker exec vigilant-ollama ollama pull nomic-embed-text:latest  # opcional (embeddings)

# Verificar modelos disponibles
docker exec vigilant-ollama ollama list
```

## Automatización con Cron

### Procesamiento Batch Nocturno

```bash
# Editar crontab
crontab -e

# Agregar tarea (ejecutar a las 2 AM)
0 2 * * * /opt/vigilant/scripts/proceso_nocturno.sh >> /opt/vigilant/logs/cron.log 2>&1
```

**Ejemplo de script (no incluido en el repo) `/opt/vigilant/scripts/proceso_nocturno.sh`:**
```bash
#!/bin/bash
set -e

WORK_DIR="/opt/vigilant"
cd "$WORK_DIR"

echo "[$(date)] Iniciando proceso nocturno"

# Conversión de videos nuevos
docker exec vigilant-app vigilant convert

# Parseo de PDFs nuevos 
docker exec vigilant-app vigilant parse

# Limpieza de archivos temporales antiguos (>7 días)
find data/tmp -type f -mtime +7 -delete

# Rotación de logs
find logs -name "*.log" -type f -mtime +30 -delete

echo "[$(date)] Proceso nocturno completado"
```

```bash
# Dar permisos de ejecución
chmod +x /opt/vigilant/scripts/proceso_nocturno.sh
```

## Monitoreo

### Healthcheck de Contenedor (opcional)

Para reinicio automático y verificación básica de que el binario está disponible dentro del contenedor, podés agregar un `healthcheck` a Docker Compose:

```yaml
# Agregar a docker-compose.yml en servicio vigilant
healthcheck:
  test: ["CMD", "vigilant", "--version"]
  interval: 60s
  timeout: 5s
  retries: 3
```

### Logs Centralizados

**Usando journald:**
```yaml
# docker-compose.yml
logging:
  driver: "journald"
  options:
    tag: "vigilant-{{.Name}}"
```

**Consultar logs:**
```bash
journalctl -u docker -f --since "1 hour ago" | grep vigilant
```

### Métricas con Prometheus (avanzado)

Si se requiere monitoreo detallado, considerar:
- Exportar métricas de CPU/RAM/Disco de contenedores
- Monitorear cola de procesamiento
- Alertas en caso de errores recurrentes

## Backup y Recuperación

### Backup Diario

```bash
#!/bin/bash
# Ejemplo de script (no incluido en el repo): /opt/vigilant/scripts/backup_diario.sh

BACKUP_DIR="/backup/vigilant"
DATE=$(date +%Y%m%d)

# Crear directorio de backup
mkdir -p "$BACKUP_DIR/$DATE"

# Backup de datos procesados
tar czf "$BACKUP_DIR/$DATE/mp4.tar.gz" /opt/vigilant/data/mp4/
tar czf "$BACKUP_DIR/$DATE/json.tar.gz" /opt/vigilant/data/json/
tar czf "$BACKUP_DIR/$DATE/reports.tar.gz" /opt/vigilant/data/reports/

# Backup de configuración
tar czf "$BACKUP_DIR/$DATE/config.tar.gz" /opt/vigilant/config/ /opt/vigilant/.env

# Limpieza de backups antiguos (retener 30 días)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completado: $BACKUP_DIR/$DATE"
```

### Recuperación

```bash
# Restaurar desde backup
DATE=20260131
BACKUP_DIR="/backup/vigilant/$DATE"

cd /opt/vigilant
tar xzf "$BACKUP_DIR/config.tar.gz" -C /
tar xzf "$BACKUP_DIR/mp4.tar.gz" -C /
tar xzf "$BACKUP_DIR/json.tar.gz" -C /
tar xzf "$BACKUP_DIR/reports.tar.gz" -C /

# Reiniciar servicios
docker compose -f docker-compose.yml restart
```

## Seguridad

### 1. Limitar Acceso a Red

```yaml
# docker-compose.yml
networks:
  vigilant-network:
    driver: bridge
    internal: true  # No acceso externo directo
```

### 2. Ejecutar como Usuario No-Root

```yaml
# Agregar a docker-compose.yml
services:
  vigilant:
    user: "1000:1000"  # UID:GID del usuario de sistema
```

### 3. Volumes Read-Only donde sea posible

Recomendado para inputs (`data/mfs` y `data/pdf`). No está activado por defecto.
Para habilitarlo, agregar `:ro` en los mounts correspondientes.

### 4. Firewall

```bash
# Permitir solo acceso local a Ollama
sudo ufw deny 11434/tcp
sudo ufw allow from 127.0.0.1 to any port 11434 proto tcp
```

### 5. Actualización Regular

```bash
# Actualizar imágenes base
docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d

# Actualizar Vigilant
cd /opt/vigilant
git pull
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

## Escalabilidad

### Procesamiento Paralelo

Vigilant no incluye un scheduler/cola interna ni mecanismos de locking para ejecución concurrente.
Si necesitas paralelizar, hazlo a nivel externo segmentando inputs (por directorios) y usando
directorios de runtime separados (especialmente `data/tmp/` y `data/reports/`) para evitar colisiones.

### Cluster Multi-Nodo (avanzado)

Para volúmenes muy altos, considerar:
- Docker Swarm o Kubernetes
- Shared storage (NFS, GlusterFS)
- Load balancer para Ollama
- Cola de trabajos (RabbitMQ, Redis)

## Troubleshooting en Producción

### Logs en Tiempo Real

```bash
# Ollama (stdout/stderr)
docker compose -f docker-compose.yml logs -f ollama

# Vigilant (archivo en host)
tail -f logs/vigilant.log
```

### Estadísticas de Recursos

```bash
# CPU/RAM de contenedores
docker stats

# Espacio en disco
docker system df
df -h /opt/vigilant/data
```

### Reinicio Seguro

```bash
# Detener servicios grace fully
docker compose -f docker-compose.yml stop

# Verificar que no hay procesos pendientes
docker compose -f docker-compose.yml ps

# Iniciar nuevamente
docker compose -f docker-compose.yml start
```

## Checklist de Deployment

- [ ] Servidor cumple requisitos de hardware
- [ ] Docker y Docker Compose instalados
- [ ] Repositorio clonado en `/opt/vigilant`
- [ ] Directorios de datos creados con permisos correctos
- [ ] Archivo `.env` configurado
- [ ] Archivo `config/local.yaml` ajustado para producción
- [ ] `docker-compose.yml` revisado
- [ ] Servicios iniciados correctamente
- [ ] Modelos de Ollama descargados
- [ ] Test de conversión exitoso
- [ ] Test de análisis exitoso
- [ ] Cron jobs configurados (si aplica)
- [ ] Backup automatizado configurado
- [ ] Logs siendo rotados correctamente
- [ ] Firewall configurado
- [ ] Monitoreo en funcionamiento (si aplica)

## Soporte

Para problemas específicos de deployment:
- Consultar `docs/10_troubleshooting.md`
- Abrir issue en GitHub con detalles del entorno
- Incluir logs relevantes (sin datos sensibles)
