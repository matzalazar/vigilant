# Formato Esperado de PDFs

## Descripción

El módulo `vigilant/parsers/pdf_parser.py` está diseñado para extraer metadata de reportes PDF generados automáticamente por sistemas de CCTV propietarios. Este documento describe el formato esperado.

## Estructura Esperada

### Campos Principales (Cabecera)

El PDF debe contener los siguientes campos en cualquier parte del documento:

```
Usuario: <nombre_usuario>
Fecha de inicio: <fecha_inicio_proceso>
Fecha de finalización: <fecha_fin_proceso>
Tipo: <tipo_proceso>
Dividir archivo: <Si/No>
Firmar: <Si/No/Sí>
Marca de agua: <Si/No/Sí>
```

### Secciones de Grabaciones

Cada grabación se identifica por el marcador `Nombre del canal:` seguido de sus metadatos:

```
Nombre del canal: <nombre>
Fecha de inicio: <fecha_inicio_grabacion>
Fecha de finalización: <fecha_fin_grabacion>
Estado: <estado>
- <path_archivo_generado>
```

## Ejemplo Completo

```
Reporte de Conversión CCTV
Usuario: admin
Fecha de inicio: 2024-01-15 08:00:00
Fecha de finalización: 2024-01-15 18:00:00
Tipo: Conversión Batch

Opciones:
Dividir archivo: No
Firmar: Sí
Marca de agua: No

Nombre del canal: Cámara 1
Fecha de inicio: 2024-01-15 08:00:00
Fecha de finalización: 2024-01-15 12:00:00
Estado: Completo
- C:/Archivos/Output/camara1_2024-01-15.mp4

Nombre del canal: Cámara 2
Fecha de inicio: 2024-01-15 12:00:00
Fecha de finalización: 2024-01-15 18:00:00
Estado: Completo
- C:/Archivos/Output/camara2_2024-01-15.mp4
```

## Manejo de Errores

### Comportamiento Robusto

A partir de la versión 0.2.0, el parser implementa manejo robusto de errores:

- **Campos faltantes**: Si un campo no se encuentra, se usa un valor por defecto
- **Formato inesperado**: Si el PDF se abre pero no contiene el formato esperado, retorna estructura con defaults
- **PDF ilegible/no abre**: El CLI registra el error y continúa con el siguiente archivo (no aborta el batch)
- **Bloques vacíos**: Se ignoran automáticamente

### Valores por Defecto

| Campo | Default |
|-------|---------|
| `usuario` | `"Desconocido"` |
| `fecha_inicio_proceso` | `""` (string vacío) |
| `fecha_fin_proceso` | `""` |
| `tipo` | `""` |
| `dividir_archivo` | `""` |
| `firmar` | `""` |
| `marca_agua` | `""` |
| `nombre_canal` | `""` |
| `fecha_inicio` (grabación) | `""` |
| `fecha_fin` (grabación) | `""` |
| `estado` | `""` |

### Uso vía CLI

```bash
# Parsear PDFs a JSON
vigilant parse --input-dir data/pdf --output-dir data/json
```

## Normalización de Paths

Los paths en `archivo_generado` son automáticamente normalizados:
- Barras invertidas (`\`) se convierten a barras normales (`/`)
- Ejemplo: `C:\Videos\file.mp4` → `C:/Videos/file.mp4`

## Notas Técnicas

### Extracción de Texto (implementación interna)

El parser usa PyMuPDF (fitz) para extraer todo el texto del PDF:

```python
doc = fitz.open(str(pdf_path))
text = "\n".join(page.get_text() for page in doc)
```

### Patrones Regex

Los patrones no son case-sensitive y buscan el campo seguido de cualquier contenido hasta fin de línea:

- Usuario: `r"Usuario: (.+)"`
- Fechas: `r"Fecha de inicio: (.+)"` y `r"Fecha de finalización: (.+)"`
- Tipo: `r"Tipo: (.+)"`
- Estado: `r"Estado: (.+)"`

### Seguridad

El parser **NO valida** ni **sanitiza** el contenido extraído. Se asume que los PDFs provienen de fuentes confiables del sistema CCTV.

> [!WARNING]
> No usar este parser con PDFs de fuentes no confiables sin validación adicional.

## Casos de Prueba

Para validar que un PDF es compatible, verificar:

1. Contiene al menos el campo "Usuario:"
2. Las fechas están en formato legible (no se parsean, solo se extraen como strings)
3. Cada grabación tiene la línea "Nombre del canal:"
4. Los paths de archivos generados empiezan con "- "

## Troubleshooting

### Problema: Usuario aparece como "Desconocido"

**Causas posibles:**
- El PDF no contiene la línea `Usuario: <nombre>`
- Hay caracteres especiales o encoding incorrecto
- El patrón no coincide exactamente

**Solución:**
Verificar que el PDF contiene exactamente `Usuario:` seguido de espacio y el nombre.

### Problema: Grabaciones vacías

**Causas posibles:**
- El PDF no contiene "Nombre del canal:"
- Los bloques están vacíos o mal formados

**Solución:**
Cada sección de grabación debe empezar explícitamente con `Nombre del canal:`.

## Changelog

### v0.2.0 (2026-01-31)
- Agregado manejo robusto de errores con `_safe_extract()`
- PDFs malformados ya no causan crashes
- Valores por defecto para todos los campos
- Type hints agregados (`Union[str, Path]` para `pdf_path`)
- Documentación mejorada con formato esperado

### v0.1.0
- Versión inicial con parsing básico (crasheaba con PDFs malformados)
