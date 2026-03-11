# Video Conversion - Proprietary to Standard Formats

This document describes the process of converting video files from proprietary CCTV formats (currently `.mfs`) to the standard MP4 format.

## Problem Solved

CCTV surveillance systems use proprietary formats that:

- Cannot be played in standard players (VLC, QuickTime, Windows Media Player)
- Require proprietary software from the manufacturer
- Hinder long-term preservation
- Complicate sharing evidence with external experts
- Are not compatible with standard forensic tools

**Solution:** Convert to standard MP4 while maintaining visual integrity and chain of custody.

## Conversion Tools

Vigilant uses two tools in cascade:

### HandBrakeCLI (Primary)

**Features:**
- High-quality conversion
- Multiple optimized presets
- Broad compatibility with codecs
- Standard MP4/MKV output

**Usage in Vigilant:**
```bash
HandBrakeCLI -i input.mfs -o output.mp4 --preset "Fast 1080p30"
```

Results vary depending on the origin and condition of the file.

### FFmpeg (Fallback/Rescue)

**Features:**
- Greater error tolerance
- Ability to ignore corrupt headers
- Raw extraction of streams

**Usage in Vigilant (bitexact remux):**
```bash
ffmpeg -y -i input.mfs -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy output.mp4
```

Results vary depending on the origin and condition of the file.

## Standard Conversion Process

### CLI - Basic Conversion

```bash
# Convert all .mfs files in input directory
vigilant convert

# Specify custom directories
vigilant convert --input-dir /evidence/raw --output-dir /evidence/processed
```

### CLI - With Rescue Mode

```bash
# Rescue mode is enabled by default: if HandBrake fails, Vigilant attempts remux and then rescue.
vigilant convert

# (Optional) Disable rescue mode (HandBrake only)
vigilant convert --no-rescue

# Output:
# ✓ normal_file.mfs → normal_file.mp4 (HandBrake)
# ⚠ corrupt_file.mfs → corrupt_file.mp4 (ffmpeg remux) or corrupt_file_forced.mp4 (ffmpeg rescue)
```

### YAML Configuration

```yaml
# config/local.yaml
handbrake:
  preset: "Fast 1080p30"  # HandBrake preset

# Note:
# - If the output file already exists, the CLI automatically skips it.
# - There are no additional conversion flags outside of those exposed by HandBrake.
```

## Generated Files

For each successful conversion, the following are generated:

### 1. Converted Video (`.mp4`)

```bash
output/
└── evidence_20260131.mp4  # Video in standard format
```

**Features:**
- Codec: H.264 by default (HandBrake); may vary in rescue
- Container: MP4
- Compatible with all standard players

### 2. Verification Hash (`.sha256`)

```bash
output/
└── evidence_20260131.mp4.sha256
```

**Content (includes optional label):**
```
# Converted Video
d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7  evidence_20260131.mp4
```

**Note:** `sha256sum -c` ignores lines starting with `#`.

**Verification:**
```bash
sha256sum -c evidence_20260131.mp4.sha256
# Output: evidence_20260131.mp4: OK
```

### 3. Forensic Metadata (`.integrity.json`)

```bash
output/
└── evidence_20260131.mp4.integrity.json
```

**Structure:**

> [!NOTE]
> `conversion.tool` reflects the actual pipeline executed. Typical values:
> - `HandBrake` (transcode only)
> - `HandBrake+ffmpeg normalize` (transcode + container metadata normalization)
> - `ffmpeg remux` / `ffmpeg rescue` (fallback/rescue)

```json
{
  "integrity_version": "1.0",
  "timestamp": "2026-01-31T14:23:45.123456+00:00",
  "source": {
    "path": "/evidence/raw/evidence_20260131.mfs",
    "filename": "evidence_20260131.mfs",
    "sha256": "a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0...",
    "size_bytes": 1258291200
  },
  "converted": {
    "path": "/evidence/processed/evidence_20260131.mp4",
    "filename": "evidence_20260131.mp4",  
    "sha256": "d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4...",
    "size_bytes": 987654321
  },
  "conversion": {
    "tool": "HandBrake+ffmpeg normalize",
    "preset": "Fast 1080p30",
    "command": "HandBrakeCLI -i /evidence/raw/evidence_20260131.mfs -o /evidence/processed/evidence_20260131.mp4 --preset 'Fast 1080p30' && ffmpeg -y -i /evidence/processed/evidence_20260131.mp4 -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy /evidence/processed/evidence_20260131_normalized.mp4",
    "tool_version": "HandBrakeCLI 1.6.1; ffmpeg 6.1",
    "rescue_mode": false
  }
}
```

## Conversion Logs

### Successful Conversion

```
[2026-01-31 14:15:00] INFO - converting path=/evidence_20260131.mfs
[2026-01-31 14:15:30] INFO - converted path=/evidence_20260131.mfs
[2026-01-31 14:15:35] INFO - original hash=a3f5e9c2... file=/evidence_20260131.mfs
[2026-01-31 14:15:35] INFO - converted hash=d9e3f6a0... file=/evidence_20260131.mp4
[2026-01-31 14:15:35] INFO - integrity saved path=/evidence_20260131.mp4.integrity.json
```

### Conversion with Rescue

```
[2026-01-31 14:20:00] INFO - converting path=/corrupted_file.mfs
[2026-01-31 14:20:10] ERROR - failure path=/corrupted_file.mfs err=codec not supported
[2026-01-31 14:20:10] INFO - failure path=/corrupted_file.mfs rescue=yes
[2026-01-31 14:20:11] INFO - remux path=/corrupted_file.mfs
[2026-01-31 14:20:12] ERROR - remux failed path=/corrupted_file.mfs
[2026-01-31 14:20:13] INFO - rescue path=/corrupted_file.mfs
[2026-01-31 14:20:45] INFO - rescue ok path=/corrupted_file.mfs
[2026-01-31 14:20:45] INFO - original hash=abc123... file=/corrupted_file.mfs
[2026-01-31 14:20:45] INFO - converted hash=def456... file=/corrupted_file_forced.mp4
[2026-01-31 14:20:45] INFO - integrity saved path=/corrupted_file_forced.mp4.integrity.json
```

## Batch Processing

### Full Directory Processing

```bash
# Input structure
evidence/raw/
├── footage_001.mfs
├── footage_002.mfs
├── footage_003.mfs
└── footage_004.mfs

# Run batch conversion
vigilant convert --input-dir evidence/raw --output-dir evidence/processed

# Output
evidence/processed/
├── footage_001.mp4
├── footage_001.mp4.sha256
├── footage_001.mp4.integrity.json
├── footage_002.mp4
├── footage_002.mp4.sha256
├── footage_002.mp4.integrity.json
...
```

### Selective Processing

```bash
# Convert entire directory
vigilant convert --input-dir data/mfs --output-dir data/mp4

# Convert a single file
# (move or copy only that file to a temporary directory and run convert)
```

**Note:** The CLI currently processes all `.mfs` files found recursively in `--input-dir`.
If the output file already exists, it is automatically skipped.

## Automation via CLI

### Individual Conversion

> [!NOTE]
> Vigilant **is only executed via CLI**. For automation, use shell scripts that call the CLI.

**Example of automation:**

```bash
#!/bin/bash
# Process new files daily
vigilant convert --input-dir /evidence/new --output-dir /evidence/converted
```

### Batch Conversion

```bash
# Batch conversion via CLI
vigilant convert --input-dir /evidence/raw --output-dir /evidence/processed
```

## Post-Conversion Verification

### Verify Integrity

```bash
# Verify hash
sha256sum -c evidence.mp4.sha256

# Verify that the video is playable
ffprobe evidence.mp4

# Play for visual inspection
vlc evidence.mp4
```

### Compare with Original

```bash
# Duration (should be similar)
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 original.mfs
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 converted.mp4

# Resolution
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 original.mfs
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 converted.mp4
```

## HandBrake Presets

### Recommended Presets

| Preset | Resolution | FPS | Speed | Size |
|--------|------------|-----|-----------|--------|
| `Fast 1080p30` | 1920x1080 | 30 | Fast | Medium |
| `Fast 720p30` | 1280x720 | 30 | Very Fast | Small |
| `HQ 1080p30` | 1920x1080 | 30 | Slow | Large |

### Configure Custom Preset

```yaml
# config/local.yaml
handbrake:
  preset: "HQ 1080p30"  # Higher quality, slower
```

### Quality/Speed Adjustments

```yaml
# For faster processing (lower quality)
handbrake:
  preset: "Very Fast 720p30"

# For maximum quality (slower)
handbrake:
  preset: "HQ 1080p30 Surround"
```

## Troubleshooting

See [10_troubleshooting.md](10_troubleshooting.md) for common conversion issues.

For files that fail even with rescue mode, see [05_rescue_mode.md](05_rescue_mode.md) for advanced techniques.

## References

- **HandBrake:** https://handbrake.fr/docs/
- **FFmpeg:** https://ffmpeg.org/documentation.html
- **MP4 Container:** ISO/IEC 14496-14

---

**Next:** [05_rescue_mode.md](05_rescue_mode.md) - Rescue pipeline for corrupt files
