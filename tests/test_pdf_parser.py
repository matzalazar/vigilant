"""
Tests para vigilant/parsers/pdf_parser.py
"""
from unittest.mock import Mock, patch, MagicMock

import pytest

from vigilant.parsers.pdf_parser import parse_pdf


class TestParsePdf:
    """Tests para la función parse_pdf."""

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_basic_structure(self, mock_fitz_open, sample_pdf_text):
        """Test de estructura básica del parsing de PDF."""
        # Configurar mock de PyMuPDF
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_pdf_text
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("fake_path.pdf")
        
        # Verificar estructura básica
        assert "usuario" in result
        assert "fecha_inicio_proceso" in result
        assert "fecha_fin_proceso" in result
        assert "tipo" in result
        assert "opciones" in result
        assert "grabaciones" in result

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_usuario(self, mock_fitz_open, sample_pdf_text):
        """Test de extracción de usuario."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_pdf_text
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("fake_path.pdf")
        
        assert result["usuario"] == "admin"

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_fechas(self, mock_fitz_open, sample_pdf_text):
        """Test de extracción de fechas."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_pdf_text
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("fake_path.pdf")
        
        assert "2024-01-15" in result["fecha_inicio_proceso"]
        assert "2024-01-15" in result["fecha_fin_proceso"]

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_opciones(self, mock_fitz_open, sample_pdf_text):
        """Test de extracción de opciones."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_pdf_text
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("fake_path.pdf")
        
        assert "dividir_archivo" in result["opciones"]
        assert "firmar" in result["opciones"]
        assert "marca_agua" in result["opciones"]
        assert result["opciones"]["dividir_archivo"] == "No"
        assert result["opciones"]["firmar"] == "Sí"

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_grabaciones(self, mock_fitz_open, sample_pdf_text):
        """Test de extracción de grabaciones."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_pdf_text
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("fake_path.pdf")
        
        assert len(result["grabaciones"]) == 2
        
        # Primera grabación
        assert result["grabaciones"][0]["nombre_canal"] == "Cámara 1"
        assert result["grabaciones"][0]["estado"] == "Completo"
        assert "camara1" in result["grabaciones"][0]["archivo_generado"]
        
        # Segunda grabación
        assert result["grabaciones"][1]["nombre_canal"] == "Cámara 2"
        assert result["grabaciones"][1]["estado"] == "Completo"
        assert "camara2" in result["grabaciones"][1]["archivo_generado"]

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_archivo_generado(self, mock_fitz_open, sample_pdf_text):
        """Test de extracción de archivos generados."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = sample_pdf_text
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("fake_path.pdf")
        
        # Verificar que los paths usan / en lugar de \\
        for grabacion in result["grabaciones"]:
            if grabacion["archivo_generado"]:
                assert "\\" not in grabacion["archivo_generado"]
                assert "/" in grabacion["archivo_generado"]

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_malformed_no_crash(self, mock_fitz_open):
        """
        Test CRÍTICO: PDF malformado NO debe crashear.
        
        Verifica el fix para el bug donde PDFs sin el formato esperado
        causaban AttributeError en re.search().group(1).
        """
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # PDF sin ninguno de los campos esperados
        mock_page.get_text.return_value = "Este PDF no tiene el formato esperado\nSolo texto random"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        # NO debe crashear, debe retornar valores por defecto
        result = parse_pdf("malformed.pdf")
        
        assert isinstance(result, dict)
        assert result["usuario"] == "Desconocido"  # Default value
        assert result["fecha_inicio_proceso"] == ""
        assert result["fecha_fin_proceso"] == ""
        assert result["tipo"] == ""
        assert isinstance(result["opciones"], dict)
        assert isinstance(result["grabaciones"], list)

    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_partial_fields_only(self, mock_fitz_open):
        """PDF con solo algunos campos debe usar defaults para faltantes."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        # Solo tiene usuario, falta todo lo demás
        mock_page.get_text.return_value = "Usuario: Partial User\nAlgunos otros datos\nPero sin campos requeridos"
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("partial.pdf")
        
        assert result["usuario"] == "Partial User"  # Found
        assert result["fecha_inicio_proceso"] == ""  # Default
        assert result["tipo"] == ""  # Default
        
    @patch("vigilant.parsers.pdf_parser.fitz.open")
    def test_parse_pdf_empty_document(self, mock_fitz_open):
        """PDF completamente vacío no debe crashear."""
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc.__iter__ = Mock(return_value=iter([mock_page]))
        mock_fitz_open.return_value = mock_doc
        
        result = parse_pdf("empty.pdf")
        
        assert isinstance(result, dict)
        assert result["usuario"] == "Desconocido"
        assert len(result["grabaciones"]) == 0

