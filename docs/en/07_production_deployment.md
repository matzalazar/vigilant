# Production Deployment

Guide for deploying Vigilant in production environments with Docker.

## Hardware Requirements

### Minimum (Conversion Only)
- CPU: 2 cores
- RAM: 4GB
- Disk: 50GB SSD
- Network: 100Mbps

### Recommended (With AI Analysis)
- CPU: 8+ cores (or GPU with CUDA/ROCm)
- RAM: 16GB (32GB if intensive analysis)
- Disk: 500GB+ NVMe SSD
- Network: 1Gbps

### Optimal (High Volume)
- CPU: 16+ cores or dedicated GPU
- RAM: 64GB
- Disk: 2TB+ NVMe RAID
- Network: 10Gbps

## Production Stack

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
│  │      Shared Volumes (data)    │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
```

> [!NOTE]
> Vigilant is **CLI-only** and does not expose its own HTTP service. If you want to control network access, the typical point to protect/expose is **Ollama** (port 11434) or the internal Docker network; a reverse proxy (Nginx/Caddy) would be an **external** and optional component, not part of the project.

## Deployment with Docker Compose

### 1. Environment Preparation

```bash
# Clone repository on server
git clone https://github.com/matzalazar/vigilant.git /opt/vigilant
cd /opt/vigilant

# Create data directories
mkdir -p data/{mfs,mp4,pdf,json,tmp,reports/md,reports/imgs}
mkdir -p logs

# Configure permissions
sudo chown -R $USER:$USER data/ logs/
```

### 2. Configuration

**Environment variables (Docker Compose):**

> [!NOTE]
> In the `docker-compose.yml` of this repo, these variables are already defined in `services.vigilant.environment`.
> The `.env` (python-dotenv) file is primarily used for **local** execution and is not automatically mounted inside the container.
```ini
# Routes inside the container (do not modify without changing volumes)
VIGILANT_INPUT_DIR=/data/mfs
VIGILANT_OUTPUT_DIR=/data/mp4
VIGILANT_INPUT_PDF_DIR=/data/pdf
VIGILANT_OUTPUT_JSON_DIR=/data/json
VIGILANT_DATA_DIR=/app/data

# Ollama (service in Docker)
VIGILANT_OLLAMA_URL=http://ollama:11434

# Logging
VIGILANT_LOG_LEVEL=INFO

# YOLO (if used)
# VIGILANT_YOLO_MODEL=/app/models/yolov8n.pt
```

**`config/local.yaml` file:**
```yaml
# Configuration optimized for production
logging:
  level: "INFO"

ai:
  ollama_url: "http://ollama:11434"
  
  # Models
  filter_backend: "yolo"  # Faster than llava for pre-filter
  filter_model: "llava:13b"
  analysis_model: "llava:13b"
  report_model: "mistral:latest"
  
  # Performance
  sample_interval: 5
  filter_min_confidence: 0.65
  
frames:
  mode: "interval+scene"
  scene_threshold: 0.05
  scale: 480  # Speed/quality balance

yolo:
  confidence: 0.30
  iou: 0.45
  device: "cpu"  # Change to "0" if GPU available

# Optimized profiles
scenario:
  camera: "fixed"
  lighting: "mixed"
  motion: true

profiles:
  - name: "standard_production"
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

The repository includes `docker-compose.yml` as a base. For production, you can apply overrides (limits, logging, read-only volumes) on top of this file.

**`docker-compose.yml`:**
```yaml
version: '3.8'

services:
  # Ollama service (AI engine)
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

  # Vigilant service (main application)
  vigilant:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: vigilant-app
    environment:
      # Ollama configuration
      - VIGILANT_OLLAMA_URL=http://ollama:11434
      # Logging level
      - VIGILANT_LOG_LEVEL=INFO
      # Data directories (inside the container)
      - VIGILANT_INPUT_DIR=/data/mfs
      - VIGILANT_OUTPUT_DIR=/data/mp4
      - VIGILANT_INPUT_PDF_DIR=/data/pdf
      - VIGILANT_OUTPUT_JSON_DIR=/data/json
      - VIGILANT_DATA_DIR=/app/data
    volumes:
      # Host -> container data directory mounting
      - ./data/mfs:/data/mfs
      - ./data/mp4:/data/mp4
      - ./data/pdf:/data/pdf
      - ./data/json:/data/json
      # Reports and temporary files (analysis)
      - ./data/tmp:/app/data/tmp
      - ./data/reports:/app/data/reports
      # Log mounting
      - ./logs:/app/logs
      # Config mounting for local overrides
      - ./config/local.yaml:/app/config/local.yaml:ro
    depends_on:
      ollama:
        condition: service_healthy
    networks:
      - vigilant-network
    # The container stays alive to execute commands
    entrypoint: [ "tail", "-f", "/dev/null" ]
    restart: unless-stopped

volumes:
  # Persistent volume for Ollama models
  ollama_data:
    driver: local

networks:
  vigilant-network:
    driver: bridge
```

### 4. Initialization

```bash
# Build images
docker compose -f docker-compose.yml build

# Start services
docker compose -f docker-compose.yml up -d

# Verify status
docker compose -f docker-compose.yml ps

# View logs
# - Ollama: stdout/stderr via Docker logs
# - Vigilant: file on host (logs/vigilant.log)
docker compose -f docker-compose.yml logs -f ollama
tail -f logs/vigilant.log
```

### 5. Download AI Models

```bash
docker exec vigilant-ollama ollama pull llava:13b
docker exec vigilant-ollama ollama pull mistral:latest
docker exec vigilant-ollama ollama pull nomic-embed-text:latest  # optional (embeddings)

# Verify available models
docker exec vigilant-ollama ollama list
```

## Automation with Cron

### Nightly Batch Processing

```bash
# Edit crontab
crontab -e

# Add task (run at 2 AM)
0 2 * * * /opt/vigilant/scripts/nightly_process.sh >> /opt/vigilant/logs/cron.log 2>&1
```

**Example script (not included in the repo) `/opt/vigilant/scripts/nightly_process.sh`:**
```bash
#!/bin/bash
set -e

WORK_DIR="/opt/vigilant"
cd "$WORK_DIR"

echo "[$(date)] Starting nightly process"

# Convert new videos
docker exec vigilant-app vigilant convert

# Parse new PDFs 
docker exec vigilant-app vigilant parse

# Clean old temporary files (>7 days)
find data/tmp -type f -mtime +7 -delete

# Log rotation
find logs -name "*.log" -type f -mtime +30 -delete

echo "[$(date)] Nightly process completed"
```

```bash
# Grant execution permissions
chmod +x /opt/vigilant/scripts/nightly_process.sh
```

## Monitoring

### Container Healthcheck (optional)

For automatic restart and basic verification that the binary is available inside the container, you can add a `healthcheck` to Docker Compose:

```yaml
# Add to docker-compose.yml in vigilant service
healthcheck:
  test: ["CMD", "vigilant", "--version"]
  interval: 60s
  timeout: 5s
  retries: 3
```

### Centralized Logs

**Using journald:**
```yaml
# docker-compose.yml
logging:
  driver: "journald"
  options:
    tag: "vigilant-{{.Name}}"
```

**Consult logs:**
```bash
journalctl -u docker -f --since "1 hour ago" | grep vigilant
```

### Metrics with Prometheus (advanced)

If detailed monitoring is required, consider:
- Exporting CPU/RAM/Disk metrics from containers
- Monitoring processing queue
- Alerts in case of recurring errors

## Backup and Recovery

### Daily Backup

```bash
#!/bin/bash
# Example script (not included in the repo): /opt/vigilant/scripts/daily_backup.sh

BACKUP_DIR="/backup/vigilant"
DATE=$(date +%Y%m%d)

# Create backup directory
mkdir -p "$BACKUP_DIR/$DATE"

# Backup processed data
tar czf "$BACKUP_DIR/$DATE/mp4.tar.gz" /opt/vigilant/data/mp4/
tar czf "$BACKUP_DIR/$DATE/json.tar.gz" /opt/vigilant/data/json/
tar czf "$BACKUP_DIR/$DATE/reports.tar.gz" /opt/vigilant/data/reports/

# Backup configuration
tar czf "$BACKUP_DIR/$DATE/config.tar.gz" /opt/vigilant/config/ /opt/vigilant/.env

# Clean old backups (retain 30 days)
find "$BACKUP_DIR" -type d -mtime +30 -exec rm -rf {} \;

echo "Backup completed: $BACKUP_DIR/$DATE"
```

### Recovery

```bash
# Restore from backup
DATE=20260131
BACKUP_DIR="/backup/vigilant/$DATE"

cd /opt/vigilant
tar xzf "$BACKUP_DIR/config.tar.gz" -C /
tar xzf "$BACKUP_DIR/mp4.tar.gz" -C /
tar xzf "$BACKUP_DIR/json.tar.gz" -C /
tar xzf "$BACKUP_DIR/reports.tar.gz" -C /

# Restart services
docker compose -f docker-compose.yml restart
```

## Security

### 1. Limit Network Access

```yaml
# docker-compose.yml
networks:
  vigilant-network:
    driver: bridge
    internal: true  # No direct external access
```

### 2. Run as Non-Root User

```yaml
# Add to docker-compose.yml
services:
  vigilant:
    user: "1000:1000"  # UID:GID of the system user
```

### 3. Read-Only Volumes where possible

Recommended for inputs (`data/mfs` and `data/pdf`). Not enabled by default.
To enable it, add `:ro` in the corresponding mounts.

### 4. Firewall

```bash
# Allow only local access to Ollama
sudo ufw deny 11434/tcp
sudo ufw allow from 127.0.0.1 to any port 11434 proto tcp
```

### 5. Regular Updates

```bash
# Update base images
docker compose -f docker-compose.yml pull
docker compose -f docker-compose.yml up -d

# Update Vigilant
cd /opt/vigilant
git pull
docker compose -f docker-compose.yml build
docker compose -f docker-compose.yml up -d
```

## Scalability

### Parallel Processing

Vigilant does not include an internal scheduler/queue or locking mechanisms for concurrent execution.
If you need to parallelize, do so at an external level by segmenting inputs (by directories) and using
separate runtime directories (especially `data/tmp/` and `data/reports/`) to avoid collisions.

### Multi-Node Cluster (advanced)

For very high volumes, consider:
- Docker Swarm or Kubernetes
- Shared storage (NFS, GlusterFS)
- Load balancer for Ollama
- Job queue (RabbitMQ, Redis)

## Production Troubleshooting

### Real-Time Logs

```bash
# Ollama (stdout/stderr)
docker compose -f docker-compose.yml logs -f ollama

# Vigilant (file on host)
tail -f logs/vigilant.log
```

### Resource Stats

```bash
# Container CPU/RAM
docker stats

# Disk space
docker system df
df -h /opt/vigilant/data
```

### Secure Restart

```bash
# Stop services gracefully
docker compose -f docker-compose.yml stop

# Verify no pending processes
docker compose -f docker-compose.yml ps

# Start again
docker compose -f docker-compose.yml start
```

## Deployment Checklist

- [ ] Server meets hardware requirements
- [ ] Docker and Docker Compose installed
- [ ] Repository cloned in `/opt/vigilant`
- [ ] Data directories created with correct permissions
- [ ] `.env` file configured
- [ ] `config/local.yaml` file adjusted for production
- [ ] `docker-compose.yml` reviewed
- [ ] Services started correctly
- [ ] Ollama models downloaded
- [ ] Successful conversion test
- [ ] Successful analysis test
- [ ] Cron jobs configured (if applicable)
- [ ] Automated backup configured
- [ ] Logs being correctly rotated
- [ ] Firewall configured
- [ ] Monitoring in place (if applicable)

## Support

For specific deployment issues:
- Consult [10_troubleshooting.md](10_troubleshooting.md)
- Open an issue on GitHub with environment details
- Include relevant logs (without sensitive data)
