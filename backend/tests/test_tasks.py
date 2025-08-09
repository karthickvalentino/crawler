
import pytest
from unittest.mock import patch, MagicMock
from src.tasks import process_page_data_task

@patch('src.tasks.insert_web_page')
@patch('src.tasks.truncate_or_pad_vector')
@patch('src.tasks.normalize')
@patch('src.tasks.create_embedding_with_ollama')
def test_process_page_data_task_html(mock_create_embedding, mock_normalize, mock_truncate, mock_insert):
    """Test processing of HTML page data."""
    mock_embedding = [0.1] * 1024
    mock_create_embedding.return_value = mock_embedding
    mock_normalize.return_value = mock_embedding
    mock_truncate.return_value = mock_embedding

    page_data = {
        "url": "http://example.com",
        "content": "This is some html content.",
        "file_type": "html",
        "embedding_type": "text",
    }
    process_page_data_task(page_data)

    mock_create_embedding.assert_called_once_with("This is some html content.")
    mock_normalize.assert_called_once_with(mock_embedding)
    mock_truncate.assert_called_once_with(mock_embedding, dims=1024)
    mock_insert.assert_called_once()


@patch('src.tasks.insert_web_page')
@patch('src.tasks.truncate_or_pad_vector')
@patch('src.tasks.normalize')
@patch('src.tasks.create_multimodal_embedding_with_ollama')
def test_process_page_data_task_image(mock_create_embedding, mock_normalize, mock_truncate, mock_insert):
    """Test processing of image page data."""
    mock_embedding = [0.2] * 1024
    mock_create_embedding.return_value = mock_embedding
    mock_normalize.return_value = mock_embedding
    mock_truncate.return_value = mock_embedding

    page_data = {
        "url": "http://example.com/image.jpg",
        "content": None,
        "file_type": "image",
        "embedding_type": "vision",
    }
    process_page_data_task(page_data)

    mock_create_embedding.assert_called_once_with("http://example.com/image.jpg")
    mock_normalize.assert_called_once_with(mock_embedding)
    mock_truncate.assert_called_once_with(mock_embedding, dims=1024)
    mock_insert.assert_called_once()
