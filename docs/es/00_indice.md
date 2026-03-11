# Índice técnico (docs/)

Este directorio contiene documentación técnica de referencia organizada en orden narrativo lógico.

## Documentación Técnica

### Fundamentos y Setup

- **[01_instalacion_y_configuracion.md](01_instalacion_y_configuracion.md)** - Requisitos, instalación y setup inicial reproducible
- **[02_chain_of_custody.md](02_chain_of_custody.md)** - Sistema de integridad forense con SHA-256 y metadata
- **[03_arquitectura_tecnica.md](03_arquitectura_tecnica.md)** - Módulos, flujo de datos y artefactos del sistema

### Conversión de Video (Core)

- **[04_conversion_de_video.md](04_conversion_de_video.md)** - Proceso de conversión de formatos propietarios a estándar
- **[05_rescue_mode.md](05_rescue_mode.md)** - Pipeline de rescate para archivos corruptos: arquitectura y técnicas

### Uso del Sistema

- **[06_guia_de_configuracion.md](06_guia_de_configuracion.md)** - Configuración avanzada (.env + YAML + perfiles)

### Producción y Consideraciones Legales

- **[07_production_deployment.md](07_production_deployment.md)** - Guía de deployment en producción con Docker
- **[08_legal_y_limitaciones.md](08_legal_y_limitaciones.md)** - Disclaimers legales, privacidad y limitaciones técnicas
- **[09_formato_pdf.md](09_formato_pdf.md)** - Especificación del formato PDF esperado y manejo de errores

### Operaciones y Mantenimiento

- **[10_troubleshooting.md](10_troubleshooting.md)** - Resolución de problemas comunes
- **[11_tests.md](11_tests.md)** - Ejecución de tests y cobertura
- **[12_docker_quickstart.md](12_docker_quickstart.md)** - Quick start con contenedores y Docker Compose

## Orden Narrativo

La documentación sigue un orden lógico de aprendizaje:

1. **Setup** (01): Instalar y configurar dependencias
2. **Fundamentos** (02): Chain of custody (base de todo procesamiento forense)
3. **Arquitectura** (03): Flujo de datos y módulos
4. **Core** (04-05): Conversión de video estándar y rescate de archivos dañados
5. **Uso avanzado** (06): Configuración detallada
6. **Producción** (07-09): Deployment profesional, consideraciones legales y formato PDF
7. **Ops** (10-12): Troubleshooting, tests y herramientas de desarrollo
8. **Ejemplos** (`examples/`): Artefactos de una corrida real anonimizados (fuera de `docs/`)
