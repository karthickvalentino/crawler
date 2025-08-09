import logging
from io import BytesIO

import fitz  # PyMuPDF
import requests
from src.embeddings import create_multimodal_embedding_with_ollama

logger = logging.getLogger(__name__)


def handle_pdf(url: str) -> dict:
    """
    Downloads a PDF from a URL, extracts its text content, and returns a dictionary
    containing the processed data.
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        if "application/pdf" not in response.headers.get("Content-Type", ""):
            logger.warning(f"URL does not point to a PDF: {url}")
            return None

        with fitz.open(stream=BytesIO(response.content), filetype="pdf") as doc:
            text = ""
            for page in doc:
                text += page.get_text()

        if not text.strip():
            logger.warning(f"No text extracted from PDF: {url}")
            # Here we could add the Tesseract fallback in the future
            return None

        return {
            "url": url,
            "content": text,
            "file_type": "pdf",
            "embedding_type": "text",
            "title": None,  # PDFs don't have titles in the same way HTML does
            "meta_description": None,
            "meta_tags": {},
        }

    except requests.RequestException as e:
        logger.error(f"Failed to download PDF {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Failed to process PDF {url}: {e}")
        return None


def handle_image(url: str) -> dict:
    """
    Identifies an image URL and returns a dictionary with metadata for the task queue.
    The actual embedding is generated asynchronously in the Celery task.
    """
    try:
        return {
            "url": url,
            "content": None,  # No text content for images
            "file_type": "image",
            "embedding_type": "vision",
            "title": None,
            "meta_description": None,
            "meta_tags": {},
        }
    except Exception as e:
        logger.error(f"Failed to create image data package for {url}: {e}")
        return None
