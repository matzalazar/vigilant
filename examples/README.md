# Vigilant - Ejemplo de Ejecución Real

Este directorio contiene artefactos anonimizados de una ejecución real de Vigilant.

## Estructura del Directorio

```
examples/
├── README.md                    # Este archivo
├── scripts/
│   └── blur_images.py          # Script para anonimizar imágenes
├── reports/
│   ├── imgs/                   # Frames detectados (anonimizados)
│   │   ├── 1234-Calle A 1300 y Calle B 500_..._i_169.jpg
│   │   ├── 1234-Calle A 1300 y Calle B 500_..._i_170.jpg
│   │   └── 1234-Calle A 1300 y Calle B 500_..._i_171.jpg
│   └── md/
│       ├── analysis_a_black_car_moving.md  # Reporte completo (corrida de ejemplo)
└── logs/
    └── vigilant.log             # Log de corrida (sanitizado)
```

## Corrida de Ejemplo (artefactos anonimizados)

> [!NOTE]
> Los artefactos en `examples/` están anonimizados. Los nombres de archivo pueden contener timestamps/IDs **ficticios o generalizados** y no deben interpretarse como fechas reales del incidente o de la ejecución.

**Escenario**: Video de cámara CCTV nocturna, intersección urbana  
**Duración**: 6 minutos  
**Prompt de búsqueda**: `"a black car moving"`  
**Objetivo**: Detectar un vehículo oscuro/negro en movimiento

## Configuración Utilizada

```yaml
# Pipeline de análisis
Backend de Filtrado: YOLO (YOLOv8n)
Detección de Movimiento: Habilitada (mín 2 frames consecutivos)
Modelo de Visión: LLaVA 13b
Generador de Reportes: Mistral

# Parámetros
Intervalo de Muestreo: 1 segundo
Modo de Frames: interval+scene
Umbral de Escena: 0.02
Confianza YOLO: 0.25
Desplazamiento Mínimo (Movimiento): 12px
Frames Mínimos (Movimiento): 2
```

## Resultados

### Detecciones

- Se detectaron frames relevantes y se confirmaron con movimiento.

### Timestamps de Detección

Se incluyen timestamps aproximados en el reporte generado.

### Hash de Integridad (Chain of Custody)

```
SHA-256: 169b6661d05992cab6c697f933cf522cea85556c6e6fe89287e952491b4be5ef
```

Este hash permite verificación externa de la integridad del video analizado (el video no está incluido en `examples/`).

## Análisis Cualitativo

### Descripción de LLaVA (Ejemplo - Frame 170)

> "La imagen muestra una calle vacía con edificios de dos pisos a cada lado.
> En el centro, un carro negro está en movimiento activo, detectado por dos
> frames consecutivos."

**Observaciones**:
- LLaVA identifica dirección y contexto del movimiento
- El análisis menciona "frames consecutivos" cuando está activo el filtro de movimiento (YOLO)
- Describe escena nocturna con detalle arquitectónico

### Informe Legal (Mistral)

El sistema intenta generar automáticamente un informe legal estructurado con:
- **Hechos Observables**: Descripción objetiva del evento
- **Coincidencias Relevantes**: Relación con el prompt de búsqueda
- **Observaciones**: Contexto temporal y espacial
- **Limitaciones**: Reconoce limitaciones de calidad de imagen

El resultado puede ser sanitizado; si el modelo no respeta el formato esperado, se descarta o quedan secciones incompletas.

Ver reporte completo en [`reports/md/analysis_a_black_car_moving.md`](reports/md/analysis_a_black_car_moving.md)

> [!NOTE]
> En runtime, el CLI genera reportes con timestamp (`analysis_<slug>_<timestamp>.md`).
> En `examples/` se guarda una copia con nombre estable para referencia.

## Privacidad y Anonimización

**Datos anonimizados**:
- Ubicaciones reemplazadas por "Calle A" y "Calle B"
- Imágenes procesadas con Gaussian Blur (radio 15px)
- Timestamps e IDs de cámara generalizados
- Video original no incluido (reducir tamaño del repo)

**Script de anonimización**: [`scripts/blur_images.py`](scripts/blur_images.py)

## Reproducir el Análisis

Para ejecutar Vigilant con tu propio video:

```bash
# 1. Instalar dependencias
pip install -r requirements.txt
pip install -e .

# 2. Configurar .env
cp .env.example .env
# Editar VIGILANT_INPUT_DIR, VIGILANT_OUTPUT_DIR, VIGILANT_YOLO_MODEL

# 3. Iniciar Ollama
ollama serve

# 4. Descargar modelos
ollama pull llava:13b
ollama pull mistral:latest

# 5. Ejecutar análisis
vigilant analyze --video /ruta/al/video.mp4 --prompt "tu búsqueda"
```

Ver [documentación completa](../README_EN.md) para más detalles.

## Lecciones Aprendidas

### Requisitos de Hardware
- **CPU-only viable**: Este análisis se ejecutó en CPU
- **RAM recomendada**: 16GB+ para LLaVA 13b
- **GPU opcional**: Podría mejorar tiempos de análisis

### Optimizaciones Aplicadas
1. **Intervalo de muestreo ajustado**: Balance entre cobertura y rendimiento
2. **Prefiltro YOLO**: Reduce los frames enviados a LLaVA
3. **Detección de movimiento**: Reduce falsos positivos en escenas estáticas
4. **Enriquecimiento de prompt**: Mejora calidad de análisis de LLaVA

### Aplicabilidad Forense
- Timestamps aproximados para ubicación temporal
- Metadata completa (índice de frame, confianza, movimiento)
- Reporte legal estructurado automático
- Cadena de custodia documentada en logs
- Hash SHA-256 para verificación de integridad

## Verificación de Integridad

> [!NOTE]
> Los archivos `.integrity.json` **no están incluidos** en `examples/` porque el video original no se incluye en el repositorio (para reducir tamaño).
> En una ejecución real, Vigilant genera automáticamente `video.mp4.integrity.json` con metadata forense completa.

Para verificar un MP4 propio:

```bash
# Linux/macOS
sha256sum video.mp4

# Windows (PowerShell)
Get-FileHash video.mp4 -Algorithm SHA256
```

## Referencias

- [Documentación completa](../docs/)
- [Arquitectura del sistema](../docs/03_arquitectura_tecnica.md)
- [Cadena de Custodia](../docs/02_chain_of_custody.md)
- [Guía de configuración](../docs/06_guia_de_configuracion.md)

---

**Nota**: Este ejemplo demuestra las capacidades reales del sistema con datos anonimizados.
Para casos de uso forense reales, consultar documentación de privacidad y compliance.
