# Docker Quickstart (Technical Reference)

## Requirements

- Docker
- Docker Compose
- 8GB RAM+
- 10GB disk+

## Quickstart

```bash
./docker-quick-start.sh start
./docker-quick-start.sh pull
cp /path/to/videos/*.mfs data/mfs/
# Convert .mfs -> .mp4 (output in data/mp4/)
./docker-quick-start.sh cmd convert
./docker-quick-start.sh cmd analyze --prompt "A dark vehicle"
```

## Commands

- `./docker-quick-start.sh start`
- `./docker-quick-start.sh pull`
- `./docker-quick-start.sh stop`
- `./docker-quick-start.sh restart`
- `./docker-quick-start.sh logs`
- `./docker-quick-start.sh status`
- `./docker-quick-start.sh cmd [...]`

## Expected Structure

```
data/
  mfs/   # inputs
  mp4/   # outputs
  pdf/
  json/
  tmp/
  reports/
    md/
    imgs/
logs/
config/local.yaml  # optional (overrides)
```

## Manual Docker Compose

> [!TIP]
> It is **recommended to use** `./docker-quick-start.sh start` instead of `docker compose up` directly.
> The helper script automatically creates the necessary directories and handles the initial setup.

If you prefer to use Docker Compose manually:

```bash
# Create directories first
mkdir -p data/{mfs,mp4,pdf,json,tmp,reports/{md,imgs}} logs

# Start services
docker compose up -d
docker compose logs -f ollama
# Vigilant logs (file on host):
tail -f logs/vigilant.log
docker exec -it vigilant-app vigilant analyze --help
docker compose down
```
