# Troubleshooting - Resolución de Problemas

Guía de solución de problemas comunes en Vigilant.

## Problemas de Conexión con Ollama

### Síntoma: "ERROR: No se puede conectar a Ollama"

```
ERROR - No se pudo conectar a Ollama en http://localhost:11434
```

**Causas posibles:**

1. **Ollama no está corriendo**
   
   Verificar:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   
   Solución:
   ```bash
   # Iniciar Ollama
   ollama serve
   
   # O en background (Linux/macOS)
   nohup ollama serve > /dev/null 2>&1 &
   ```

2. **Ollama corriendo en puerto diferente**
   
   Verificar puerto:
   ```bash
   ps aux | grep ollama
   lsof -i :11434
   ```
   
   Solución - configurar puerto correcto en `.env`:
   ```ini
   VIGILANT_OLLAMA_URL="http://localhost:PUERTO_CORRECTO"
   ```

3. **Firewall bloqueando conexión**
   
   Solución (Ubuntu/Debian):
   ```bash
   sudo ufw allow 11434/tcp
   ```

### Síntoma: "Modelo no encontrado"

```
ERROR - Modelo llava:13b no disponible
```

**Solución:**

```bash
# Verificar modelos instalados
ollama list

# Descargar modelo faltante
ollama pull llava:13b
ollama pull mistral:latest
```

## Problemas de Conversión

### Síntoma: "HandBrakeCLI no encontrado"

```
ERROR - HandBrakeCLI no está en PATH
```

**Solución Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install handbrake-cli
```

**Solución macOS:**
```bash
brew install handbrake
```

**Verificar instalación:**
```bash
which HandBrakeCLI
HandBrakeCLI --version
```

### Síntoma: Conversión falla con "codec not supported"

```
WARNING - HandBrake falló, intentando rescate
ERROR - No se pudo decodificar video
```

**Causas posibles:**

1. **Archivo corrupto parcialmente**
   
   Solución automática (ya incluida):
   ```bash
   # Vigilant intenta rescate automático (por defecto)
   vigilant convert
   ```

2. **Formato completamente desconocido**
   
   Diagnóstico manual:
   ```bash
   ffprobe input.mfs
   ```
   
   Si no hay salida coherente, el archivo puede estar corrupto o encriptado.

3. **Falta codec específico**
   
   Solución - instalar ffmpeg completo:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

### Síntoma: Videos convertidos sin audio

**Causa:** Preset de HandBrake no incluye audio o source no tiene audio.

**Verificar source:**
```bash
ffprobe -show_streams input.mfs | grep audio
```

**Solución:** Ajustar preset en `config/local.yaml`:
```yaml
handbrake:
  preset: "Fast 1080p30"  # Incluye audio AAC
```

## Problemas de Performance

### Síntoma: Análisis muy lento (>5min por imagen)

**Diagnóstico:**

1. **Verificar carga de CPU:**
   ```bash
   htop
   # Buscar proceso ollama
   ```

2. **Verificar modelo usado:**
   ```bash
   # Modelos más grandes = más lentos
   # llava:13b ~4-5s/frame (CPU)
   # llava:7b  ~2-3s/frame (CPU)
   ```

**Soluciones:**

1. **Usar modelo más pequeño (menos precisión):**
   ```yaml
   # config/local.yaml
   ai:
     filter_model: "llava:7b"  # Más rápido que 13b
   ```

2. **Aumentar intervalo de muestreo:**
   ```yaml
   ai:
     sample_interval: 10  # Analizar cada 10s en vez de 5s
   ```

3. **Usar modo solo intervalo (sin scene detection):**
   ```yaml
   frames:
     mode: "interval"  # Más rápido que "interval+scene"
   ```

4. **Considerar GPU (si disponible):**
   - Ollama soporta GPU automáticamente si detecta CUDA/ROCm
   - Speedup típico: 5-10x

### Síntoma: Memoria insuficiente

```
ERROR - Out of memory
killed
```

**Soluciones:**

1. **Reducir tamaño de modelo:**
   ```bash
   ollama pull llava:7b  # En vez de 13b
   ```

2. **Reducir escala de frames:**
   ```yaml
   frames:
     scale: 360  # En vez de 480 o 640
   ```

3. **Procesar videos en lotes más pequeños:**
   ```bash
   # En vez de procesar 50 videos a la vez
   # Procesar de a 10
   ```

## Problemas de Permisos

### Síntoma: "Permission denied" al escribir archivos

```
ERROR - PermissionError: [Errno 13] Permission denied: '/output/video.mp4'
```

**Soluciones:**

1. **Verificar perm isos de directorio:**
   ```bash
   ls -ld /output/
   ```

2. **Ajustar permisos:**
   ```bash
   sudo chown -R $USER:$USER /output/
   chmod -R u+w /output/
   ```

3. **En Docker:**
   ```bash
   # Ejecutar contenedor con usuario correcto
   docker compose down
   # Editar docker-compose.yml:
   # user: "1000:1000"  # UID:GID de tu usuario
   docker compose up -d
   ```

### Síntoma: "Permission denied" al leer archivos

**Causa:** Archivos pertenecen a otro usuario (común al copiar desde USB).

**Solución:**
```bash
sudo chown -R $USER:$USER /input/
chmod -R u+r /input/
```

## Problemas de Calidad de Análisis

### Síntoma: Muchos falsos positivos

**Soluciones:**

1. **Aumentar umbral de confianza:**
   ```yaml
   ai:
     filter_min_confidence: 0.70  # Default: 0.60
   ```

2. **Mejorar especificidad del prompt:**
   ```bash
   # Antes (vago):
   vigilant analyze --prompt "auto"
   
   # Después (específico):
   vigilant analyze --prompt "Sedan oscuro, probablemente negro o gris oscuro"
   ```

3. **Usar YOLO como prefiltro:**
   ```yaml
   ai:
     filter_backend: "yolo"  # Más preciso que LLaVA para objetos comunes
   ```

### Síntoma: No detecta objetos obvios (falsos negativos)

**Soluciones:**

1. **Reducir umbral:**
   ```yaml
   ai:
     filter_min_confidence: 0.50
   ```

2. **Usar modo scene detection:**
   ```yaml
   frames:
     mode: "scene"  # Captura todos los cambios visuales
     scene_threshold: 0.02  # Más sensible
   ```

3. **Reducir intervalo de muestreo:**
   ```yaml
   ai:
     sample_interval: 3  # Cada 3 segundos
   ```

## Problemas de Docker

### Síntoma: "Cannot connect to Docker daemon"

**Solución:**
```bash
# Iniciar Docker
sudo systemctl start docker

# Agregar usuario a grupo docker (evitar sudo)
sudo usermod -aG docker $USER
# Logout y login para aplicar
```

### Síntoma: Contenedores no se inician

```bash
# Ver logs
docker compose logs ollama
# Vigilant escribe logs en archivo (host):
tail -n 200 logs/vigilant.log

# Ver estado
docker compose ps

# Reiniciar servicios
docker compose down
docker compose up -d
```

### Síntoma: "dial tcp: lookup ollama: no such host"

**Causa:** El contenedor vigilant no puede resolver el nombre del servicio ollama.

**Solución:**
```bash
# Verificar que ambos estén en la misma network
docker network inspect vigilant-network

# Recrear network
docker compose down
docker compose up -d
```

## Problemas de Logs

### No se generan logs en `logs/vigilant.log`

**Causa:** Directorio no existe o sin permisos.

**Solución:**
```bash
mkdir -p logs
chmod u+w logs
```

### Logs muy verbosos

**Solución - reducir nivel:**
```ini
# .env
VIGILANT_LOG_LEVEL="WARNING"  # Solo warnings y errors
```

### Necesito más detalles en logs

**Solución - aumentar nivel:**
```ini
# .env
VIGILANT_LOG_LEVEL="DEBUG"
```

## Verificación de Integridad

### Síntoma: Hash no coincide después de transferencia

```bash
# Calcular hash local
vigilant convert  # Genera .sha256

# Después de copiar a otro sistema
sha256sum video.mp4
# No coincide con archivo .sha256
```

**Causa:** Archivo corrupto durante transferencia.

**Solución:**
```bash
# Retransferir con verificación
rsync -avz --checksum origen/ destino/
```

## Debugging Avanzado

### Habilitar logging máximo

```bash
export VIGILANT_LOG_LEVEL="DEBUG"
vigilant analyze --prompt "..." 2>&1 | tee debug.log
```

### Verificar configuración cargada

- Revisar `config/default.yaml` y `config/local.yaml` (overrides).
- Verificar variables de entorno activas (`.env` o entorno de shell).
- Ejecutar `vigilant --check` para validar dependencias y conexión con Ollama.

### Testear conectividad Ollama manualmente

```bash
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llava:13b",
  "prompt": "Describe this image",
  "images": []
}'
```

## Obtener Ayuda

Si el problema persiste:

1. **Revisa documentación completa:** `docs/00_indice.md`
2. **Busca issues existentes:** GitHub Issues
3. **Crea nuevo issue con:**
   - Descripción del problema
   - Pasos para reproducir
   - Logs relevantes (`logs/vigilant.log`)
   - Configuración (sin datos sensibles)
   - Salida de `vigilant --version`
   - SO y versión de Python
   - Versión de Ollama (`ollama --version`)

## Comandos Útiles de Diagnóstico

```bash
# Verificar todas las dependencias
which python ffmpeg HandBrakeCLI
python --version
ffmpeg -version
HandBrakeCLI --version
ollama --version

# Verificar instalación de Vigilant
vigilant --version
pip show vigilant

# Verificar modelos Ollama
ollama list

# Verificar espacio en disco
df -h

# Verificar uso de memoria
free -h

# Ver procesos de Ollama
ps aux | grep ollama

# Test rápido
vigilant analyze --help
```
