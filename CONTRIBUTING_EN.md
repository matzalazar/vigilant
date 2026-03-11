# Contributing to Vigilant

Thank you for your interest in contributing to Vigilant. This document provides basic guidelines for contributing to the project.

## Code of Conduct

- Use professional and respectful language
- Accept constructive criticism with grace
- Focus on what is best for the project

## Reporting Bugs

Before creating an issue:
1. Verify that it has not been previously reported
2. Ensure you are using the latest version
3. Review the documentation to confirm it is a bug

When reporting a bug, include:
- Clear description of the problem
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs (from `logs/vigilant.log`)
- Environment (OS, Python, Vigilant version, Ollama version)

## Suggesting Enhancements

For new features:
1. Open an issue describing the problem it would solve
2. Explain why it is important
3. Provide usage examples

## Pull Requests

### Preparation

```bash
# 1. Fork and clone
git clone https://github.com/YOUR_USER/vigilant.git
cd vigilant

# 2. Create branch
git checkout -b feature/my-feature

# 3. Environment setup
pip install -e ".[dev]"
```

### Development

1. **Write quality code**:
   - Follow PEP 8 (use `ruff check .`)
   - Add type hints to public functions
   - Document with docstrings

2. **Add tests**:
   ```bash
   pytest -v --cov=vigilant
   ```

3. **Update documentation** if you change functionality

### Commits

Use descriptive messages with prefixes:

```bash
git commit -m "feat: add support for .avi format"
git commit -m "fix: correct hash calculation on Windows"
git commit -m "docs: update configuration guide"
```

**Prefixes:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Add or modify tests
- `refactor:` - Refactoring
- `chore:` - Maintenance

### Submit PR

```bash
git push origin feature/my-feature
```

On GitHub, create the Pull Request with:
- Descriptive title
- Description of changes
- Reference to related issues (#123)

## Code Style

### Python

```python
from pathlib import Path
from typing import Optional

def process_video(
    video_path: Path,
    output_dir: Path,
    preset: Optional[str] = None
) -> Path:
    """
    Processes a video file.
    
    Args:
        video_path: Path to the input video
        output_dir: Output directory
        preset: Conversion preset (optional)
    
    Returns:
        Path of the processed file
    """
    if not video_path.exists():
        raise FileNotFoundError(f"Video not found: {video_path}")
    
    return output_dir / f"{video_path.stem}.mp4"
```

**Principles:**
- Type hints in public functions
- Docstrings in Google format
- Descriptive names

### Tests

```python
def test_calculate_sha256_valid_file(tmp_path):
    """SHA-256 calculation must be correct."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    hash_result = calculate_sha256(test_file)
    
    assert len(hash_result) == 64
    assert hash_result.islower()
```

## Full Local Setup

```bash
# Clone
git clone https://github.com/matzalazar/vigilant.git
cd vigilant

# Virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in development mode
pip install -e ".[dev]"

# Optional: YOLO
pip install ".[yolo]"

# Linting
ruff check .
ruff format .
```

## Contact

- Issues: [GitHub Issues](https://github.com/matzalazar/vigilant/issues)
- Discussions: [GitHub Discussions](https://github.com/matzalazar/vigilant/discussions)

## License

By contributing to Vigilant, you agree that your contributions will be licensed under GPL-3.0.

---

Thank you for contributing to Vigilant.
