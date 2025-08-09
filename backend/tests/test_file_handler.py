import pytest
from unittest.mock import patch, MagicMock
import requests
from src.crawlers.file_handler import handle_pdf, handle_image

@pytest.fixture
def mock_requests_get():
    """Fixture to mock requests.get"""
    with patch('requests.get') as mock_get:
        yield mock_get

def test_handle_pdf_success(mock_requests_get):
    """Test successful handling of a PDF file."""
    # Mock the response from requests.get
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/pdf'}
    # A minimal valid PDF file content
    mock_response.content = b'%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000103 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n149\n%%EOF'

    mock_requests_get.return_value = mock_response

    # Mock fitz.open
    with patch('fitz.open') as mock_fitz_open:
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = "This is a test."
        mock_doc.__enter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        result = handle_pdf("http://example.com/test.pdf")

        assert result is not None
        assert result["url"] == "http://example.com/test.pdf"
        assert result["content"] == "This is a test."
        assert result["file_type"] == "pdf"
        assert result["embedding_type"] == "text"

def test_handle_pdf_download_fails(mock_requests_get):
    """Test that handle_pdf returns None when the download fails."""
    mock_requests_get.side_effect = requests.RequestException("Download failed")

    result = handle_pdf("http://example.com/test.pdf")
    assert result is None

def test_handle_pdf_not_a_pdf(mock_requests_get):
    """Test that handle_pdf returns None for non-PDF content."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'text/html'}
    mock_response.content = b'<html></html>'
    mock_requests_get.return_value = mock_response

    result = handle_pdf("http://example.com/test.html")
    assert result is None

def test_handle_pdf_no_text(mock_requests_get):
    """Test that handle_pdf returns None when no text can be extracted."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.headers = {'Content-Type': 'application/pdf'}
    mock_response.content = b'%PDF-1.0...'
    mock_requests_get.return_value = mock_response

    with patch('fitz.open') as mock_fitz_open:
        mock_doc = MagicMock()
        mock_page = MagicMock()
        mock_page.get_text.return_value = ""
        mock_doc.__enter__.return_value = [mock_page]
        mock_fitz_open.return_value = mock_doc

        result = handle_pdf("http://example.com/test.pdf")
        assert result is None

@patch('src.crawlers.file_handler.create_multimodal_embedding_with_ollama')
def test_handle_image_success(mock_create_embedding):
    """Test successful handling of an image file."""
    result = handle_image("http://example.com/test.jpg")

    assert result is not None
    assert result["url"] == "http://example.com/test.jpg"
    assert result["content"] is None
    assert result["file_type"] == "image"
    assert result["embedding_type"] == "vision"
    assert "embedding" not in result
    mock_create_embedding.assert_not_called()
