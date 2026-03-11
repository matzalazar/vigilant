> 🇪🇸 [Versión en español](README_ES.md)

![Vigilant header](assets/vigilant_header.png)

# Vigilant — Forensic Video Processing Suite

![License](https://img.shields.io/badge/license-GPL--3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Tests](https://github.com/matzalazar/vigilant/workflows/Tests/badge.svg)
![Platform](https://img.shields.io/badge/platform-linux%20%7C%20macos-lightgrey.svg)

**Vigilant** is a professional forensic video processing suite that converts proprietary CCTV formats to open standards, with local AI-assisted visual analysis and automated chain of custody for conversions. Designed for investigators, forensic analysts, and security professionals requiring traceability and independent verification.

## System Architecture

```mermaid
graph LR
    subgraph IN["Input"]
        MFS[.mfs CCTV]
        PDF[PDF]
    end

    subgraph CONV["Conversion"]
        HB[HandBrake]
        RES[Rescue]
        HASH[SHA-256]
        META[Metadata]
    end

    subgraph AI["AI Analysis (optional)"]
        FR[Frames]
        YO[YOLO]
        LL[LLaVA]
        RP[Report]
    end

    subgraph OUT["Output"]
        MP4[.mp4]
        SHA[.sha256]
        JSON[.json]
        MD[.md]
    end

    MFS --> HB
    HB -->|ok| HASH
    HB -->|fail| RES --> HASH
    HASH --> META
    HASH --> MP4 --> SHA
    META --> JSON
    PDF -.-> JSON

    MP4 -.-> FR --> YO --> LL --> RP --> MD
```

## Key Features

### 1. Forensic Conversion (Core Project)

**Problem solved:** Proprietary CCTV systems generate files in closed formats (currently `.mfs`) that cannot be played in standard players. This makes it difficult to:
- Review evidence on forensic equipment
- Long-term preservation
- Presentation in legal proceedings
- Share with external experts

**Vigilant's solution:**

```mermaid
flowchart LR
    A[.mfs Video<br/>Proprietary] --> B{HandBrakeCLI}
    B -->|Success| C[Clean<br/>Conversion]
    B -->|Failure| D[Rescue Mode]
    D --> E{Stream<br/>Analysis}
    E --> F[FFmpeg<br/>Extraction]
    F --> G[Partial<br/>Recovery]
    C --> H[SHA-256]
    G --> H
    H --> I[.mp4 + .sha256<br/>+ .integrity.json]
```

**Conversion features:**

- **Multi-tool:** HandBrakeCLI as primary, FFmpeg as fallback
- **Rescue pipeline:** Automatic recovery of corrupted or partially damaged files
- **Forensic integrity:** SHA-256 of source and destination calculated automatically
- **Complete metadata:** Tool, preset, command, version, timestamps, and sizes recorded
- **Reproducibility:** Container metadata normalized and commands recorded to reduce variation across runs
- **Batch processing:** Mass conversion of complete directories

**Generated files per conversion:**

```bash
input/
  └── footage_2024_01_15.mfs

output/
  ├── footage_2024_01_15.mp4
  ├── footage_2024_01_15.mp4.sha256
  └── footage_2024_01_15.mp4.integrity.json
```

**Example forensic metadata (`*.integrity.json`):**

```json
{
  "integrity_version": "1.0",
  "timestamp": "2026-01-31T14:23:45.123456+00:00",
  "source": {
    "path": "/input/footage_2024_01_15.mfs",
    "filename": "footage_2024_01_15.mfs",
    "sha256": "a3f5e9c2d1b8f4e6a9c0d5e8f1a4b7c2...",
    "size_bytes": 1258291200
  },
  "converted": {
    "path": "/output/footage_2024_01_15.mp4",
    "filename": "footage_2024_01_15.mp4",
    "sha256": "d9e3f6a0b5c8d2e7f1a6b9c4d8e3f7a2...",
    "size_bytes": 987654321
  },
  "conversion": {
    "tool": "HandBrake+ffmpeg normalize",
    "preset": "Fast 1080p30",
    "command": "HandBrakeCLI -i /input/footage_2024_01_15.mfs -o /output/footage_2024_01_15.mp4 --preset 'Fast 1080p30' && ffmpeg -y -i /output/footage_2024_01_15.mp4 -map_metadata -1 -map_chapters -1 -fflags +bitexact -flags:v +bitexact -flags:a +bitexact -c copy /output/footage_2024_01_15_normalized.mp4",
    "tool_version": "HandBrakeCLI 1.6.1; ffmpeg 6.1",
    "rescue_mode": false
  }
}
```


### 2. AI-Powered Visual Analysis (Complementary Feature)

**Problem solved:** Manually reviewing hours of CCTV video is impractical. Assistance is needed to quickly identify relevant frames.

**Vigilant's solution:**

```mermaid
flowchart TD
    A[Video .mp4] --> B[Frame Extraction N segs + scene]
    
    B --> C{Prefilter}

    C -->|YOLO| D[Object detection: person, vehicle]
    C -->|LLaVA quick| E[Fast keyword matching]

    D --> F{Match?}
    E --> F

    F -->|Yes| G[Deep analysis with LLaVA detailed]
    F -->|No| H[Discard frame]

    G --> I[Legal-format report with Mistral]
    I --> J[Markdown + screenshots]
```

**Analysis features:**

- **Local and offline:** Ollama runs models on your machine, no cloud data transfer
- **Two prefilter modes:** YOLO (fast, common objects) or LLaVA (flexible, any criteria)
- **Motion detection (YOLO-only, optional):** Additional context for dynamic objects (when `ai.filter_backend=yolo` and motion is enabled)
- **Deep analysis:** Detailed forensic descriptions of relevant frames
- **Legal-format reports (AI-assisted):** Professional format generated by Mistral
- **Semantic embeddings (optional):** Similarity-based filtering to reduce false positives (when `ai.use_embeddings=true`)

**Important note:** AI analysis is an **investigative assistance tool**. Results must be reviewed by qualified professionals. It does not replace human judgment.

### 3. Chain of Custody

- SHA-256 hashes of source and conversion
- `.sha256` files in standard format (compatible with `sha256sum`, optional comment/label line)
- Complete forensic metadata (`.integrity.json`)
- Command and tool version recorded in metadata
- UTC timestamps and transformation logging
- Post-transfer integrity verification

### 4. PDF Processing

- Metadata extraction from PDF reports
- Structured JSON conversion
- Preparation for manual correlation with video evidence

## Technical Scope

- **Inputs**: `.mfs` (CCTV), `.pdf` (reports)
- **Outputs**: `.mp4`, `.json` (metadata), markdown reports + screenshots
- **Integrity**: SHA-256, conversion metadata, UTC timestamps
- **AI**: LLaVA for analysis, Mistral for reports, optional YOLO prefilter
- **Modes**: Offline, reproducible, no cloud dependencies

## System Requirements

### Core Software
- Python 3.8 or higher
- `ffmpeg` (video processing)
- `HandBrakeCLI` (primary conversion)
- [Ollama](https://ollama.com/) (local AI engine, required only for `vigilant analyze`)

### Optional Dependencies
- `ultralytics` + YOLO model (fast prefilter)
- Docker + Docker Compose (containerized deployment)

### Recommended AI Models
```bash
ollama pull llava:13b        # Visual analysis
ollama pull mistral:latest   # Report generation
ollama pull nomic-embed-text # Semantic embeddings (optional)
```

## Quick Installation

### Local Installation

```bash
# Clone the repository
git clone https://github.com/matzalazar/vigilant.git
cd vigilant

# Install core dependencies
pip install -r requirements.txt
pip install -e .

# Verify installation
vigilant --version

# Verify external dependencies
vigilant --check
```

### Automated Setup

```bash
# Full installation with virtual environment and YOLO
./scripts/setup.sh --with-yolo --download-yolo

# CPU-only (no GPU)
./scripts/setup.sh --with-yolo --cpu-only
```

### Docker (Recommended for Production)

```bash
# Start services (Vigilant + Ollama)
docker compose up -d

# Check status
docker compose ps

# (Optional) Convert evidence .mfs -> .mp4 (if there are files in data/mfs/)
docker exec vigilant-app vigilant convert

# Run analysis
docker exec vigilant-app vigilant analyze --prompt "person with vest"
```

> In Docker mode, environment variables (paths, `VIGILANT_OLLAMA_URL`, etc.) are configured in `docker-compose.yml` (or overrides). The `.env` file is mainly for local execution (python-dotenv).

Complete documentation: [`docs/en/12_docker_quickstart.md`](docs/en/12_docker_quickstart.md)

## Configuration

### Environment Variables (`.env`)

```ini
# Input/output paths (required)
VIGILANT_INPUT_DIR="/mnt/evidence/raw"
VIGILANT_OUTPUT_DIR="/mnt/evidence/processed"

# YOLO model (optional)
VIGILANT_YOLO_MODEL="/path/to/yolov8n.pt"

# Logging level (optional, default: INFO)
VIGILANT_LOG_LEVEL="DEBUG"

# AI Analysis (optional)
VIGILANT_OLLAMA_URL="http://localhost:11434"
VIGILANT_ANALYSIS_MODEL="llava:13b"
```

### YAML Files

- `config/default.yaml`: Default configuration (versioned)
- `config/local.yaml`: Local overrides (ignored by git)

**Precedence**: `default.yaml` → `local.yaml` → environment variables

Complete documentation: [`docs/en/06_configuration_guide.md`](docs/en/06_configuration_guide.md)

## Usage

### Video Conversion

```bash
# Convert all .mfs files in input directory
# (Automatic rescue: enabled by default)
vigilant convert

# (Optional) Disable automatic rescue
vigilant convert --no-rescue

# Output: .mp4 files + .sha256 + .integrity.json
```

### PDF Report Parsing

```bash
# Extract metadata from PDF reports to JSON
vigilant parse

# Output: .json files with structured metadata
```

### AI Visual Analysis

```bash
# Search for specific object/person
vigilant analyze --prompt "Dark vehicle in motion"

# Analyze specific file
vigilant analyze --video evidence.mp4 --prompt "Person with red backpack"

# Output:
# - Report: data/reports/md/analysis_<slug>_<timestamp>.md
# - Screenshots: data/reports/imgs/
# Note: the "Legal report (AI)" section is sanitized; if it is discarded, the report will say so.
```

> `data/` and `logs/` are treated as runtime directories (inputs/outputs) and are not committed to git.
> For a real run with anonymized artifacts included in the repository, see `examples/`.

## Architecture

```
vigilant/
├── core/           # Configuration, logging, forensic integrity
├── converters/     # HandBrake, FFmpeg, rescue pipeline
├── parsers/        # PDF metadata extraction
└── intelligence/   # AI analysis (frame extraction, LLaVA, YOLO)
```

**Processing flow**:
1. Conversion (`.mfs` → `.mp4` with chain of custody)
2. Frame extraction (interval/scene/hybrid)
3. Optional prefilter (YOLO or fast LLaVA)
4. Deep analysis (detailed LLaVA)
5. Report generation (Mistral in legal format)

Complete documentation: [`docs/en/03_technical_architecture.md`](docs/en/03_technical_architecture.md)

## Testing

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run full test suite
pytest -v

# With coverage
pytest -v --cov=vigilant --cov-report=term-missing

# Fast tests only
pytest -v -m "not slow"
```

Complete documentation: [`docs/en/11_tests.md`](docs/en/11_tests.md)

## Documentation

### Technical Documentation (`docs/`)
- [00_index.md](docs/en/00_index.md) - Documentation index
- [01_installation_and_configuration.md](docs/en/01_installation_and_configuration.md) - Detailed setup
- [02_chain_of_custody.md](docs/en/02_chain_of_custody.md) - Forensic integrity and chain of custody
- [03_technical_architecture.md](docs/en/03_technical_architecture.md) - System design
- [06_configuration_guide.md](docs/en/06_configuration_guide.md) - Configuration reference
- [10_troubleshooting.md](docs/en/10_troubleshooting.md) - Troubleshooting
- [11_tests.md](docs/en/11_tests.md) - Running tests
- [12_docker_quickstart.md](docs/en/12_docker_quickstart.md) - Docker deployment

## Use Cases

**Forensic Investigations**
- Convert proprietary CCTV evidence to standard formats
- Quick search for people/vehicles in hours of footage
- Generate legal-format reports (AI-assisted) with SHA-256 and traceability

**Security Analysis**
- Retrospective incident review
- Suspicious pattern identification
- Manual event correlation with PDF reports

**Archival and Preservation**
- Migrate proprietary formats to open standards
- Long-term integrity verification
- Forensic metadata for traceability

## Non-Goals

This project does **NOT** include:
- Graphical user interface (GUI)
- Real-time streaming
- Cloud processing
- Integrations with proprietary systems beyond file level
- Automated decision-making (this is an investigative assistance tool)

## Professional Services & Support

If your institution requires deploying **Vigilant** in a production environment, I offer specialized services including:

- **Setup & Implementation:** Configuration of air-gapped forensic workstations and hardware optimization for local AI.
- **Technical Training:** Chain of custody workflows, SHA-256 integrity management, and vision model usage for evidence analysis.
- **Process Consulting:** Adapting the suite to specific investigative workflows.

Contact me via [LinkedIn](https://www.linkedin.com/in/matzalazar/) or [matzalazar.com](https://matzalazar.com).

### Support the project

**Vigilant** is free and open source software. If this tool has been useful in an investigation or you want to support further development:

[![Buy me a coffee](https://img.shields.io/badge/Buy%20me%20a%20coffee-FF813F?style=for-the-badge&logo=buy-me-a-coffee&logoColor=white)](https://cafecito.app/matzalazar)

## Contributing

Contributions are welcome. Please read `CONTRIBUTING_EN.md` for details about our code of conduct and pull request process.

## License

This project is licensed under GPL-3.0. See `LICENSE` file for details.

**Note on forensic use**: This software is an investigative assistance tool. Results must be reviewed by qualified professionals. It does not replace human judgment or physical chain of custody.

## Author

**Matías L. Zalazar**

## Additional Resources

- [Complete Documentation](docs/en/00_index.md)
- [Issues and Support](https://github.com/matzalazar/vigilant/issues)
- [Examples](examples/)
