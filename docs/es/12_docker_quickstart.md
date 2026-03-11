# Docker Quickstart (referencia técnica)

## Requisitos

- Docker
- Docker Compose
- 8GB RAM+
- 10GB disco+

## Inicio rápido

```bash
./docker-quick-start.sh start
./docker-quick-start.sh pull
cp /ruta/a/videos/*.mfs data/mfs/
# Convertir .mfs -> .mp4 (salida en data/mp4/)
./docker-quick-start.sh cmd convert
./docker-quick-start.sh cmd analyze --prompt "Un vehículo oscuro"
```

## Comandos

- `./docker-quick-start.sh start`
- `./docker-quick-start.sh pull`
- `./docker-quick-start.sh stop`
- `./docker-quick-start.sh restart`
- `./docker-quick-start.sh logs`
- `./docker-quick-start.sh status`
- `./docker-quick-start.sh cmd [...]`

## Estructura esperada

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
config/local.yaml  # opcional (overrides)
```

## Docker Compose manual

> [!TIP]
> Se **recomienda usar** `./docker-quick-start.sh start` en lugar de `docker compose up` directamente.
> El script helper crea automáticamente los directorios necesarios y maneja el setup inicial.

Si prefieres usar Docker Compose manualmente:

```bash
# Crear directorios primero
mkdir -p data/{mfs,mp4,pdf,json,tmp,reports/{md,imgs}} logs

# Iniciar servicios
docker compose up -d
docker compose logs -f ollama
# Logs de Vigilant (archivo en host):
tail -f logs/vigilant.log
docker exec -it vigilant-app vigilant analyze --help
docker compose down
```
