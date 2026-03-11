# Troubleshooting

Guide to solving common problems in Vigilant.

## Connection Problems with Ollama

### Symptom: "ERROR: Cannot connect to Ollama"

```
ERROR - Could not connect to Ollama at http://localhost:11434
```

**Possible causes:**

1. **Ollama is not running**
   
   Verify:
   ```bash
   curl http://localhost:11434/api/tags
   ```
   
   Solution:
   ```bash
   # Start Ollama
   ollama serve
   
   # Or in background (Linux/macOS)
   nohup ollama serve > /dev/null 2>&1 &
   ```

2. **Ollama running on a different port**
   
   Verify port:
   ```bash
   ps aux | grep ollama
   lsof -i :11434
   ```
   
   Solution - configure correct port in `.env`:
   ```ini
   VIGILANT_OLLAMA_URL="http://localhost:CORRECT_PORT"
   ```

3. **Firewall blocking connection**
   
   Solution (Ubuntu/Debian):
   ```bash
   sudo ufw allow 11434/tcp
   ```

### Symptom: "Model not found"

```
ERROR - Model llava:13b not available
```

**Solution:**

```bash
# Verify installed models
ollama list

# Download missing model
ollama pull llava:13b
ollama pull mistral:latest
```

## Conversion Problems

### Symptom: "HandBrakeCLI not found"

```
ERROR - HandBrakeCLI is not in PATH
```

**Ubuntu/Debian Solution:**
```bash
sudo apt update
sudo apt install handbrake-cli
```

**macOS Solution:**
```bash
brew install handbrake
```

**Verify installation:**
```bash
which HandBrakeCLI
HandBrakeCLI --version
```

### Symptom: Conversion fails with "codec not supported"

```
WARNING - HandBrake failed, attempting rescue
ERROR - Could not decode video
```

**Possible causes:**

1. **Partially corrupt file**
   
   Automatic solution (already included):
   ```bash
   # Vigilant attempts automatic rescue (by default)
   vigilant convert
   ```

2. **Completely unknown format**
   
   Manual diagnosis:
   ```bash
   ffprobe input.mfs
   ```
   
   If there is no coherent output, the file may be corrupt or encrypted.

3. **Missing specific codec**
   
   Solution - install full ffmpeg:
   ```bash
   # Ubuntu/Debian
   sudo apt install ffmpeg
   
   # macOS
   brew install ffmpeg
   ```

### Symptom: Converted videos without audio

**Cause:** HandBrake preset does not include audio or source has no audio.

**Verify source:**
```bash
ffprobe -show_streams input.mfs | grep audio
```

**Solution:** Adjust preset in `config/local.yaml`:
```yaml
handbrake:
  preset: "Fast 1080p30"  # Includes AAC audio
```

## Performance Problems

### Symptom: Very slow analysis (>5min per image)

**Diagnosis:**

1. **Verify CPU load:**
   ```bash
   htop
   # Look for ollama process
   ```

2. **Verify model used:**
   ```bash
   # Larger models = slower
   # llava:13b ~4-5s/frame (CPU)
   # llava:7b  ~2-3s/frame (CPU)
   ```

**Solutions:**

1. **Use a smaller model (less precision):**
   ```yaml
   # config/local.yaml
   ai:
     filter_model: "llava:7b"  # Faster than 13b
   ```

2. **Increase sampling interval:**
   ```yaml
   ai:
     sample_interval: 10  # Analyze every 10s instead of 5s
   ```

3. **Use interval-only mode (without scene detection):**
   ```yaml
   frames:
     mode: "interval"  # Faster than "interval+scene"
   ```

4. **Consider GPU (if available):**
   - Ollama supports GPU automatically if it detects CUDA/ROCm
   - Typical speedup: 5-10x

### Symptom: Insufficient memory

```
ERROR - Out of memory
killed
```

**Solutions:**

1. **Reduce model size:**
   ```bash
   ollama pull llava:7b  # Instead of 13b
   ```

2. **Reduce frame scale:**
   ```yaml
   frames:
     scale: 360  # Instead of 480 or 640
   ```

3. **Process videos in smaller batches:**
   ```bash
   # Instead of processing 50 videos at once
   # Process 10 at a time
   ```

## Permission Problems

### Symptom: "Permission denied" when writing files

```
ERROR - PermissionError: [Errno 13] Permission denied: '/output/video.mp4'
```

**Solutions:**

1. **Verify directory permissions:**
   ```bash
   ls -ld /output/
   ```

2. **Adjust permissions:**
   ```bash
   sudo chown -R $USER:$USER /output/
   chmod -R u+w /output/
   ```

3. **In Docker:**
   ```bash
   # Run container with correct user
   docker compose down
   # Edit docker-compose.yml:
   # user: "1000:1000"  # Your user's UID:GID
   docker compose up -d
   ```

### Symptom: "Permission denied" when reading files

**Cause:** Files belong to another user (common when copying from USB).

**Solution:**
```bash
sudo chown -R $USER:$USER /input/
chmod -R u+r /input/
```

## Analysis Quality Problems

### Symptom: Many false positives

**Solutions:**

1. **Increase confidence threshold:**
   ```yaml
   ai:
     filter_min_confidence: 0.70  # Default: 0.60
   ```

2. **Improve prompt specificity:**
   ```bash
   # Before (vague):
   vigilant analyze --prompt "auto"
   
   # After (specific):
   vigilant analyze --prompt "Dark sedan, probably black or dark gray"
   ```

3. **Use YOLO as a pre-filter:**
   ```yaml
   ai:
     filter_backend: "yolo"  # More precise than LLaVA for common objects
   ```

### Symptom: Does not detect obvious objects (false negatives)

**Solutions:**

1. **Reduce threshold:**
   ```yaml
   ai:
     filter_min_confidence: 0.50
   ```

2. **Use scene detection mode:**
   ```yaml
   frames:
     mode: "scene"  # Captures all visual changes
     scene_threshold: 0.02  # More sensitive
   ```

3. **Reduce sampling interval:**
   ```yaml
   ai:
     sample_interval: 3  # Every 3 seconds
   ```

## Docker Problems

### Symptom: "Cannot connect to Docker daemon"

**Solution:**
```bash
# Start Docker
sudo systemctl start docker

# Add user to docker group (avoid sudo)
sudo usermod -aG docker $USER
# Logout and login to apply
```

### Symptom: Containers do not start

```bash
# View logs
docker compose logs ollama
# Vigilant writes logs to file (host):
tail -n 200 logs/vigilant.log

# View status
docker compose ps

# Restart services
docker compose down
docker compose up -d
```

### Symptom: "dial tcp: lookup ollama: no such host"

**Cause:** The vigilant container cannot resolve the ollama service name.

**Solution:**
```bash
# Verify both are on the same network
docker network inspect vigilant-network

# Recreate network
docker compose down
docker compose up -d
```

## Log Problems

### No logs generated in `logs/vigilant.log`

**Cause:** Directory does not exist or lacks permissions.

**Solution:**
```bash
mkdir -p logs
chmod u+w logs
```

### Very verbose logs

**Solution - reduce level:**
```ini
# .env
VIGILANT_LOG_LEVEL="WARNING"  # Only warnings and errors
```

### Need more details in logs

**Solution - increase level:**
```ini
# .env
VIGILANT_LOG_LEVEL="DEBUG"
```

## Integrity Verification

### Symptom: Hash mismatch after transfer

```bash
# Calculate local hash
vigilant convert  # Generates .sha256

# After copying to another system
sha256sum video.mp4
# Does not match .sha256 file
```

**Cause:** File corrupt during transfer.

**Solution:**
```bash
# Re-transfer with verification
rsync -avz --checksum source/ destination/
```

## Advanced Debugging

### Enable maximum logging

```bash
export VIGILANT_LOG_LEVEL="DEBUG"
vigilant analyze --prompt "..." 2>&1 | tee debug.log
```

### Verify loaded configuration

- Review `config/default.yaml` and `config/local.yaml` (overrides).
- Verify active environment variables (`.env` or shell environment).
- Run `vigilant --check` to validate dependencies and connection with Ollama.

### Manually test Ollama connectivity

```bash
curl -X POST http://localhost:11434/api/generate -d '{
  "model": "llava:13b",
  "prompt": "Describe this image",
  "images": []
}'
```

## Getting Help

If the problem persists:

1. **Review complete documentation:** [00_index.md](00_index.md)
2. **Search existing issues:** GitHub Issues
3. **Create a new issue with:**
   - Problem description
   - Steps to reproduce
   - Relevant logs (`logs/vigilant.log`)
   - Configuration (without sensitive data)
   - `vigilant --version` output
   - OS and Python version
   - Ollama version (`ollama --version`)

## Useful Diagnostic Commands

```bash
# Verify all dependencies
which python ffmpeg HandBrakeCLI
python --version
ffmpeg -version
HandBrakeCLI --version
ollama --version

# Verify Vigilant installation
vigilant --version
pip show vigilant

# Verify Ollama models
ollama list

# Verify disk space
df -h

# Verify memory usage
free -h

# See Ollama processes
ps aux | grep ollama

# Quick test
vigilant analyze --help
```
