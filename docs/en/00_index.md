# Technical Index (docs/)

This directory contains technical reference documentation organized in a logical narrative order.

## Technical Documentation

### Fundamentals and Setup

- **[01_installation_and_configuration.md](01_installation_and_configuration.md)** - Requirements, installation, and reproducible initial setup
- **[02_chain_of_custody.md](02_chain_of_custody.md)** - Forensic integrity system with SHA-256 and metadata
- **[03_technical_architecture.md](03_technical_architecture.md)** - Modules, data flow, and system artifacts

### Video Conversion (Core)

- **[04_video_conversion.md](04_video_conversion.md)** - Process of converting proprietary formats to standard
- **[05_rescue_mode.md](05_rescue_mode.md)** - Rescue pipeline for corrupt files: architecture and techniques

### System Usage

- **[06_configuration_guide.md](06_configuration_guide.md)** - Advanced configuration (.env + YAML + profiles)

### Production and Legal Considerations

- **[07_production_deployment.md](07_production_deployment.md)** - Guide for production deployment with Docker
- **[08_legal_and_limitations.md](08_legal_and_limitations.md)** - Legal disclaimers, privacy, and technical limitations
- **[09_pdf_format.md](09_pdf_format.md)** - Specification of the expected PDF format and error handling

### Operations and Maintenance

- **[10_troubleshooting.md](10_troubleshooting.md)** - Resolution of common problems
- **[11_tests.md](11_tests.md)** - Test execution and coverage
- **[12_docker_quickstart.md](12_docker_quickstart.md)** - Quick start with containers and Docker Compose

## Narrative Order

The documentation follows a logical learning order:

1. **Setup** (01): Install and configure dependencies
2. **Fundamentals** (02): Chain of custody (the basis of all forensic processing)
3. **Architecture** (03): Data flow and modules
4. **Core** (04-05): Standard video conversion and rescue of damaged files
5. **Advanced Usage** (06): Detailed configuration
6. **Production** (07-09): Professional deployment, legal considerations, and PDF format
7. **Ops** (10-12): Troubleshooting, tests, and development tools
8. **Examples** (`examples/`): Anonymized artifacts from a real run (outside of `docs/`)
