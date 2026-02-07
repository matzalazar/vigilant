# Tests (referencia técnica)

## Dependencias

```bash
pip install -e ".[dev]"
```

## Ejecutar suite completa

```bash
pytest tests/ -v
```

## Cobertura

```bash
pytest tests/ -v --cov=vigilant --cov-report=term-missing
```

## Ejecutar por archivo/clase/test

```bash
pytest tests/test_config.py -v
pytest tests/test_config.py::TestDeepMerge -v
pytest tests/test_config.py::TestDeepMerge::test_deep_merge_basic -v
```

## Estructura de tests

- `tests/test_config.py`
- `tests/test_logger.py`
- `tests/test_integrity.py`
- `tests/test_handbrake.py`
- `tests/test_rescue.py`
- `tests/test_frame_extractor.py`
- `tests/test_pdf_parser.py`
- `tests/test_cli.py`
- `tests/test_security.py`
