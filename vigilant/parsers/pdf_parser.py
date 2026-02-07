from vigilant.core.runtime import require_cli
require_cli()

# parsers/pdf_parser.py

import fitz
import re
from typing import Union
from pathlib import Path


def _safe_extract(pattern: str, text: str, default: str = "") -> str:
    """
    Extrae valor de regex de forma segura sin crashear.
    
    Args:
        pattern: Patrón regex a buscar
        text: Texto donde buscar
        default: Valor por defecto si no se encuentra
        
    Returns:
        Valor extraído o default si no hay match
    """
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else default


def parse_pdf(pdf_path: Union[str, Path]) -> dict:
    """
    Extrae metadata de un PDF generado automáticamente.
    
    Formato esperado del PDF:
    - Usuario: <nombre>
    - Fecha de inicio: <fecha>
    - Fecha de finalización: <fecha>
    - Tipo: <tipo>
    - Dividir archivo: <si/no>
    - Firmar: <si/no>
    - Marca de agua: <si/no>
    - Secciones con "Nombre del canal:" seguido de metadatos

    Args:
        pdf_path: Ruta al archivo .pdf.

    Returns:
        dict: Estructura del reporte parseado con valores por defecto si faltan campos.
        
    Note:
        Si el PDF no tiene el formato esperado, retorna valores por defecto
        en lugar de crashear.
    """
    doc = fitz.open(str(pdf_path))
    try:
        text = "\n".join(page.get_text() for page in doc)
    finally:
        # fitz.Document supports close(); tests may mock fitz.open without context manager support.
        try:
            doc.close()
        except Exception:
            pass

    reporte = {
        "usuario": _safe_extract(r"Usuario: (.+)", text, "Desconocido"),
        "fecha_inicio_proceso": _safe_extract(r"Fecha de inicio: (.+)", text, ""),
        "fecha_fin_proceso": _safe_extract(r"Fecha de finalización: (.+)", text, ""),
        "tipo": _safe_extract(r"Tipo: (.+)", text, ""),
        "opciones": {
            "dividir_archivo": _safe_extract(r"Dividir archivo: (.+)", text, ""),
            "firmar": _safe_extract(r"Firmar: (.+)", text, ""),
            "marca_agua": _safe_extract(r"Marca de agua: (.+)", text, ""),
        },
        "grabaciones": []
    }

    bloques = text.split("Nombre del canal:")[1:]

    for bloque in bloques:
        lines = bloque.strip().splitlines()
        if not lines:
            continue
            
        archivo_generado = None
        match_archivo = re.search(r"- (.+)", bloque)
        if match_archivo:
            archivo_generado = match_archivo.group(1).strip().replace("\\", "/")

        reporte["grabaciones"].append({
            "nombre_canal": lines[0].strip() if lines else "",
            "fecha_inicio": _safe_extract(r"Fecha de inicio: (.+)", bloque, ""),
            "fecha_fin": _safe_extract(r"Fecha de finalización: (.+)", bloque, ""),
            "estado": _safe_extract(r"Estado: (.+)", bloque, ""),
            "archivo_generado": archivo_generado
        })

    return reporte
