# Vigilant - Real Execution Example

This directory contains anonymized artifacts from a real execution of Vigilant.

## Directory Structure

```
examples/
├── README.md                    # This file
├── scripts/
│   └── blur_images.py          # Script to anonymize images
├── reports/
│   ├── imgs/                   # Detected frames (anonymized)
│   │   ├── 1234-A St 1300 and B St 500_..._i_169.jpg
│   │   ├── 1234-A St 1300 and B St 500_..._i_170.jpg
│   │   └── 1234-A St 1300 and B St 500_..._i_171.jpg
│   └── md/
│       ├── analysis_a_black_car_moving.md  # Full report (example run)
└── logs/
    └── vigilant.log             # Execution log (sanitized)
```

## Example Run (Anonymized Artifacts)

> [!NOTE]
> The artifacts in `examples/` are anonymized. File names may contain **fictitious or generalized** timestamps/IDs and should not be interpreted as actual incident or execution dates.

**Scenario**: CCTV camera video at night, urban intersection  
**Duration**: 6 minutes  
**Search Prompt**: `"a black car moving"`  
**Objective**: Detect a dark/black vehicle in motion

## Configuration Used

```yaml
# Analysis pipeline
Filtering Backend: YOLO (YOLOv8n)
Motion Detection: Enabled (min 2 consecutive frames)
Vision Model: LLaVA 13b
Report Generator: Mistral

# Parameters
Sampling Interval: 1 second
Frame Mode: interval+scene
Scene Threshold: 0.02
YOLO Confidence: 0.25
Minimum Displacement (Motion): 12px
Minimum Frames (Motion): 2
```

## Results

### Detections

- Relevant frames were detected and confirmed with motion.

### Detection Timestamps

Approximate timestamps are included in the generated report.

### Integrity Hash (Chain of Custody)

```
SHA-256: 169b6661d05992cab6c697f933cf522cea85556c6e6fe89287e952491b4be5ef
```

This hash allows for external verification of the integrity of the analyzed video (the video is not included in `examples/`).

## Qualitative Analysis

### LLaVA Description (Example - Frame 170)

> "The image shows an empty street with two-story buildings on each side.
> In the center, a black car is in active motion, detected by two
> consecutive frames."

**Observations**:
- LLaVA identifies direction and context of motion.
- The analysis mentions "consecutive frames" when the motion filter (YOLO) is active.
- Describes the night scene with architectural detail.

### Legal Report (Mistral)

The system attempts to automatically generate a structured legal report with:
- **Observable Facts**: Objective description of the event.
- **Relevant Matches**: Relation to the search prompt.
- **Observations**: Temporal and spatial context.
- **Limitations**: Recognizes image quality limitations.

The result may be sanitized; if the model does not respect the expected format, it is discarded or sections remain incomplete.

View full report at [`reports/md/analysis_a_black_car_moving.md`](reports/md/analysis_a_black_car_moving.md)

> [!NOTE]
> In runtime, the CLI generates reports with a timestamp (`analysis_<slug>_<timestamp>.md`).
> A copy with a stable name is kept in `examples/` for reference.

## Privacy and Anonymization

**Anonymized Data**:
- Locations replaced by "A St" and "B St".
- Images processed with Gaussian Blur (15px radius).
- Generalized timestamps and camera IDs.
- Original video not included (to reduce repo size).

**Anonymization script**: [`scripts/blur_images.py`](scripts/blur_images.py)

## Reproduce the Analysis

To run Vigilant with your own video:

```bash
# 1. Install dependencies
pip install -r requirements.txt
pip install -e .

# 2. Configure .env
cp .env.example .env
# Edit VIGILANT_INPUT_DIR, VIGILANT_OUTPUT_DIR, VIGILANT_YOLO_MODEL

# 3. Start Ollama
ollama serve

# 4. Download models
ollama pull llava:13b
ollama pull mistral:latest

# 5. Execute analysis
vigilant analyze --video /path/to/video.mp4 --prompt "your search"
```

See the [complete documentation](../README.md) for more details.

## Lessons Learned

### Hardware Requirements
- **CPU-only viable**: This analysis was performed on a CPU.
- **Recommended RAM**: 16GB+ for LLaVA 13b.
- **Optional GPU**: Could improve analysis times.

### Applied Optimizations
1. **Adjusted sampling interval**: Balance between coverage and performance.
2. **YOLO pre-filter**: Reduces the frames sent to LLaVA.
3. **Motion detection**: Reduces false positives in static scenes.
4. **Prompt enrichment**: Improves LLaVA analysis quality.

### Forensic Applicability
- Approximate timestamps for temporal location.
- Complete metadata (frame index, confidence, motion).
- Automatic structured legal report.
- Chain of custody documented in logs.
- SHA-256 hash for integrity verification.

## Integrity Verification

> [!NOTE]
> The `.integrity.json` files **are not included** in `examples/` because the original video is not included in the repository (to reduce size).
> In a real execution, Vigilant automatically generates `video.mp4.integrity.json` with complete forensic metadata.

To verify your own MP4:

```bash
# Linux/macOS
sha256sum video.mp4

# Windows (PowerShell)
Get-FileHash video.mp4 -Algorithm SHA256
```

## References

- [Complete Documentation](../docs/en/)
- [System Architecture](../docs/en/03_technical_architecture.md)
- [Chain of Custody](../docs/en/02_chain_of_custody.md)
- [Configuration Guide](../docs/en/06_configuration_guide.md)

---

**Note**: This example demonstrates the real capabilities of the system with anonymized data.
For actual forensic use cases, consult privacy and compliance documentation.
