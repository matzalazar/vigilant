# Chain of Custody - Forensic Integrity System

This document describes Vigilant's forensic integrity system, designed to maintain a complete and verifiable chain of custody for digital evidence.

## Introduction

In forensic investigations and legal proceedings, it is critical to demonstrate that the evidence **has not been altered** since its original capture. Vigilant implements an automated chain of custody system based on:

- **Cryptographic hashes** (SHA-256) of evidence files (source + converted)
- Complete **forensic metadata** in JSON format
- **Traceability** of all transformations
- **Independent verification** with standard tools

## System Features

### 1. Automatic SHA-256 Hash Calculation

Vigilant automatically calculates SHA-256 hashes of:

- **Source file** (`.mfs` proprietary)
- **Converted file** (`.mp4` standard)
- Generates an associated **`.sha256`** file for the converted `.mp4` (contains the `.mp4` hash)

> [!NOTE]
> Analysis reports (`.md`) and screenshots (`.jpg`) are **not** automatically hashed.
> If complete traceability of these artifacts is required, it is recommended to calculate additional hashes manually.

**Technical characteristics:**
- Algorithm: SHA-256 (NIST FIPS 180-4)
- Length: 256 bits (64 hexadecimal characters)
- Chunk size: 8KB (memory efficiency)
- Performance: ~100MB/s on modern CPU

**Implementation (internal snippet, not public API):**

```python
def calculate_sha256(file_path: Path, chunk_size: int = 8192) -> str:
    """
    Calculates SHA-256 of a file efficiently.
    
    Uses streaming read (8KB chunks) to minimize memory footprint.
    """
    sha256_hash = hashlib.sha256()
    
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()
```

### 2. Generated Integrity Files

#### `.sha256` File (Standard Format)

Format compatible with GNU/Linux `sha256sum`. Vigilant adds an optional comment line (label) before the hash:

```text
# Converted Video
a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2  video.mp4
```

**Note:** `sha256sum -c` ignores lines starting with `#`.

**Verification with standard tools:**

```bash
# Linux/macOS
sha256sum -c video.mp4.sha256

# Windows PowerShell (ignore comment lines)
$expected = Get-Content video.mp4.sha256 |
  Where-Object { $_ -notmatch '^#' } |
  ForEach-Object { $_.Split(" ")[0] } |
  Select-Object -First 1
$actual = (Get-FileHash video.mp4 -Algorithm SHA256).Hash.ToLower()
if ($expected -eq $actual) { "OK" } else { "FAILED" }
```

#### `.integrity.json` File (Complete Forensic Metadata)

JSON structure with detailed information:

```json
{
  "integrity_version": "1.0",
  "timestamp": "2026-01-31T14:23:45.123456+00:00",
  "source": {
    "path": "evidence/original_cctv_footage.mfs",
    "filename": "original_cctv_footage.mfs",
    "sha256": "a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2",
    "size_bytes": 1258291200
  },
  "converted": {
    "path": "processed/original_cctv_footage.mp4",
    "filename": "original_cctv_footage.mp4",
    "sha256": "d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7",
    "size_bytes": 987654321
  },
  "conversion": {
    "tool": "HandBrake+ffmpeg normalize",
    "preset": "Fast 1080p30",
    "command": "HandBrakeCLI -i evidence/original_cctv_footage.mfs -o processed/original_cctv_footage.mp4 --preset 'Fast 1080p30' && ffmpeg -y -i processed/original_cctv_footage.mp4 -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy processed/original_cctv_footage_normalized.mp4",
    "tool_version": "HandBrakeCLI 1.6.1; ffmpeg 6.1",
    "rescue_mode": false
  }
}
```

**Fields:**
- `integrity_version`: Metadata schema version
- `timestamp`: ISO 8601 UTC timestamp of the conversion moment
- `source`: Information about the original file
  - `path`: File path (as executed; can be absolute or relative)
  - `filename`: Filename
  - `sha256`: Full hash of the original file
  - `size_bytes`: Size in bytes
- `converted`: Information about the converted file (same structure)
- `conversion`: Conversion details
  - `tool`: Tool used (HandBrake, FFmpeg)
  - `preset`: Applied conversion preset
  - `command`: Command executed (includes metadata normalization if applicable)
  - `tool_version`: Version(s) of the tool(s) used
  - `rescue_mode`: `true` if rescue mode was used

### 3. Inclusion in Analysis Reports

When an AI analysis report is generated, the SHA-256 hash is automatically included:

```markdown
# Analysis Report - 2026-01-31 14:30:00

## Analyzed Video

- **File**: `evidence_20260131.mp4`
- **SHA-256**: `d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7`
- **Duration**: 00:06:00
- **Analyzed frames**: 72
- **Criteria**: person with red backpack

...
```

This allows correlating the report with the exact file analyzed.

## Forensic Workflow

### Step 1: Evidence Reception

```bash
$ ls evidence/
incident_2026_01_31.mfs

$ sha256sum evidence/incident_2026_01_31.mfs
a3f5e9c2...  evidence/incident_2026_01_31.mfs
```

**Document:** Record the hash of the received file in the evidence log.

### Step 2: Conversion with Chain of Custody

```bash
$ vigilant convert --input-dir evidence/ --output-dir processed/

[2026-01-31 14:15:00] INFO - Processing: incident_2026_01_31.mfs
[2026-01-31 14:15:05] INFO - Original hash: a3f5e9c2... file=incident_2026_01_31.mfs
[2026-01-31 14:15:30] INFO - Successful conversion with HandBrake
[2026-01-31 14:15:35] INFO - Converted hash: d9e3f6a0... file=incident_2026_01_31.mp4
[2026-01-31 14:15:35] INFO - Metadata saved: incident_2026_01_31.mp4.integrity.json
```

### Step 3: Verification of Generated Files

```bash
$ ls processed/
incident_2026_01_31.mp4
incident_2026_01_31.mp4.sha256
incident_2026_01_31.mp4.integrity.json

$ cat processed/incident_2026_01_31.mp4.sha256
# Converted Video
d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2...  incident_2026_01_31.mp4

$ sha256sum -c processed/incident_2026_01_31.mp4.sha256
incident_2026_01_31.mp4: OK
```

### Step 4: Secure Transfer

```bash
# Before transferring
$ sha256sum processed/incident_2026_01_31.mp4 > transfer_hash.txt

# Transfer file + hash
$ scp processed/incident_2026_01_31.mp4 forensic-server:evidence/
$ scp processed/incident_2026_01_31.mp4.integrity.json forensic-server:evidence/
$ scp transfer_hash.txt forensic-server:evidence/

# On destination server: verify
$ ssh forensic-server
$ cd /evidence
$ sha256sum incident_2026_01_31.mp4
d9e3f6a0...  incident_2026_01_31.mp4

$ # Compare with transfer_hash.txt - they must match
```

### Step 5: Legal Documentation

**Excerpt from legal report:**

> *"A video file was received in proprietary `.mfs` format with SHA-256 hash `a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2`.*
>
> *The file was converted to standard MP4 format using the tool Vigilant v0.2.0 with the HandBrakeCLI backend, 'Fast 1080p30' preset, without alteration of the visual content.*
>
> *The resulting file `incident_2026_01_31.mp4` has SHA-256 hash `d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7`.*
>
> *The integrity of the file was verified on 2026-01-31 at 15:00 UTC through independent SHA-256 hash calculation, with a positive result."*

## Standards Alignment

Vigilant implements **SHA-256** and records conversion metadata. This **helps align with** forensic practices, but **does not constitute certification or guarantee** regulatory compliance by itself (it depends on organization processes and controls).

| Reference | Actual Coverage | Notes |
|------------|----------------|-------|
| **NIST FIPS 180-4** | Implemented | SHA-256 usage for hashes |
| **RFC 6234** | Implemented | Standard SHA-2 implementation |
| **ISO 27037 / forensic guides** | Partial | Provides hashes + metadata, but does not replace procedures |

**References:**
- [NIST FIPS 180-4](https://csrc.nist.gov/publications/detail/fips/180/4/final)
- [ISO 27037:2012](https://www.iso.org/standard/44381.html)
- [NIST Computer Forensics Tool Testing](https://www.nist.gov/itl/ssd/software-quality-group/computer-forensics-tool-testing-program-cftt)
- [RFC 6234 - SHA-2](https://www.rfc-editor.org/rfc/rfc6234)

## Usage (CLI)

Integrity files are automatically generated when using the CLI:

```bash
vigilant convert --input-dir data/mfs --output-dir data/mp4
```

The `.integrity.json` and `.sha256` files are created in the same directory as the resulting MP4 file.

### Integrity Verification

```bash
# Verify hash with standard tool
sha256sum -c evidence.mp4.sha256
```

## Best Practices

### 1. Preserve Original Files

**Wrong:**
```bash
vigilant convert && rm -rf evidence/
```

**Right:**
```bash
vigilant convert
# Original files remain intact
```

### 2. Document Hashes in Case Log

Example log entry:

```
=== Evidence Log Entry #42 ===
Date: 2026-01-31 14:00 UTC
Case ID: INV-2026-0131
Operator: J. Smith

Original File:
  Name: incident_2026_01_31.mfs
  Size: 1,258,291,200 bytes
  SHA-256: a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2

Conversion:
  Tool: Vigilant v0.2.0 (HandBrake backend)
  Timestamp: 2026-01-31 14:15:35 UTC
  
Converted File:
  Name: incident_2026_01_31.mp4
  Size: 987,654,321 bytes
  SHA-256: d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2b5c8d1e4f7a0c3d6e9b2f5a8d1e4f7

Verification: PASSED (2026-01-31 15:00 UTC)
```

### 3. Verify Before Archiving

```bash
# Before moving to long-term storage
cd processed/
sha256sum -c *.sha256

# Should show:
# incident_2026_01_31.mp4: OK
```

### 4. Store Configuration

Save a configuration snapshot alongside metadata:

```bash
cp config/local.yaml processed/incident_2026_01_31_config_snapshot.yaml
```

### 5. Maintain Chain of Custody

Example of a complete chain of custody log:

```
2026-01-31 08:00 UTC - Evidence received from field (hash: a3f5e9c2...)
2026-01-31 14:15 UTC - Converted to MP4 (hash: d9e3f6a0...)
2026-01-31 14:30 UTC - Transferred to secure storage
2026-01-31 15:00 UTC - Integrity verified (SHA-256 match)
2026-02-01 09:00 UTC - Analyzed with AI assistant
2026-02-01 10:00 UTC - Re-verified integrity (SHA-256 match)
2026-02-01 14:00 UTC - Report submitted to case file
```

## Performance Impact

| File Size | Hash Calculation Time | Memory Usage |
|-----------|----------------------|--------------|
| 100 MB | ~1 second | 8 KB |
| 1 GB | ~10 seconds | 8 KB |
| 10 GB | ~100 seconds (~1.5 min) | 8 KB |

**Characteristics:**
- Overhead: ~1-2 seconds for every 100MB
- Throughput: ~100MB/s on modern CPU (Intel i5 or higher)
- Memory footprint: Constant 8KB (streaming, does not load full file)

## Troubleshooting

### Error: Permission Denied

```
WARNING - hash calculation failed path=/video.mp4 err=Permission denied
```

**Solution:**
```bash
# Verify permissions
ls -l /video.mp4

# Grant read permissions
chmod 644 /video.mp4
```

### Error: Hash Mismatch After Transfer

```bash
$ sha256sum transferred_file.mp4
xyz789...  transferred_file.mp4

# ✗ Does not match documented hash
```

**Common causes:**
- Corruption during network transfer
- Disk I/O error
- File inadvertently modified

**Solution:**
```bash
# Re-transfer the file
# Use automatic verification in scp/rsync:
rsync -avz --checksum source.mp4 destination/
```

### File Locked by Another Process

```
ERROR - Cannot calculate hash: file is locked
```

**Solution:**
```bash
# Linux: identify process
lsof /path/to/file.mp4

# Close the program that has the file open
```

## Conclusion

Vigilant's chain of custody system provides:

- **Automation** of hash calculation (source + converted)
- **Standard format** compatible with forensic tools
- **Rich metadata** for audits
- **Independent verification** without dependency on Vigilant
- **Partial alignment** with standards and best practices (NIST, ISO)

This **does not constitute certification** nor does it guarantee legal validity by itself (it depends on procedures, controls, and jurisdiction), but it **helps support** the integrity and traceability of generated artifacts and their verification by third parties.
