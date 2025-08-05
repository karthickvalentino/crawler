import pytest
from unittest.mock import patch, MagicMock
import uuid
from src.tasks import run_crawler_task, process_page_data_task

@pytest.fixture
def mock_db_update():
    """Mock the database update function."""
    with patch('src.tasks.update_job') as mock_update:
        yield mock_update

@pytest.fixture
def mock_run_scrapy_crawl():
    """Mock the run_scrapy_crawl function."""
    with patch('src.tasks.run_scrapy_crawl') as mock_crawl:
        yield mock_crawl

def test_run_crawler_task_success(mock_db_update, mock_run_scrapy_crawl):
    """
    Test the successful execution of the crawler task.
    """
    job_id = str(uuid.uuid4())
    domain = "example.com"
    depth = 1
    flags = {}

    run_crawler_task(job_id, domain, depth, flags)

    # Check that the job status is updated to running and then completed
    assert mock_db_update.call_count == 2
    
    # Check the 'running' status update
    running_call = mock_db_update.call_args_list[0]
    assert running_call[0][0] == uuid.UUID(job_id)
    assert running_call[0][1].status == 'running'

    # Check the 'completed' status update
    completed_call = mock_db_update.call_args_list[1]
    assert completed_call[0][0] == uuid.UUID(job_id)
    assert completed_call[0][1].status == 'completed'

    # Check that the crawler was called with the correct parameters
    mock_run_scrapy_crawl.assert_called_once_with(
        start_urls=[f"https://{domain}"],
        allowed_domains=[domain],
        depth_limit=depth
    )

def test_run_crawler_task_failure(mock_db_update, mock_run_scrapy_crawl):
    """
    Test the failure scenario of the crawler task.
    """
    job_id = str(uuid.uuid4())
    domain = "example.com"
    depth = 1
    flags = {}

    # Simulate an exception during crawler execution
    mock_run_scrapy_crawl.side_effect = Exception("Crawler failed")

    with pytest.raises(Exception, match="Crawler failed"):
        run_crawler_task(job_id, domain, depth, flags)

    # Check that the job status is updated to failed
    failed_call = mock_db_update.call_args_list[1]
    assert failed_call[0][0] == uuid.UUID(job_id)
    assert failed_call[0][1].status == 'failed'
    assert failed_call[0][1].result['error'] == 'Crawler failed'

@patch('src.tasks.insert_web_page')
@patch('src.tasks.truncate_or_pad_vector')
@patch('src.tasks.normalize')
@patch('src.tasks.create_embedding_with_ollama')
def test_process_page_data_task(mock_create_embedding, mock_normalize, mock_truncate, mock_insert):
    # Arrange
    page_data = {
        "url": "http://example.com",
        "title": "Example Domain",
        "meta_description": "Example Description",
        "meta_tags": {"og:title": "Example Domain"},
        "content": "This is the content of the page.",
    }
    
    mock_embedding = [0.1, 0.2, 0.3]
    mock_create_embedding.return_value = mock_embedding
    mock_normalize.return_value = mock_embedding
    mock_truncate.return_value = mock_embedding

    # Act
    process_page_data_task(page_data)

    # Assert
    mock_create_embedding.assert_called_once_with(page_data["content"])
    mock_normalize.assert_called_once_with(mock_embedding)
    mock_truncate.assert_called_once_with(mock_embedding, dims=1024)
    
    expected_db_data = {
        "url": page_data["url"],
        "title": page_data["title"],
        "meta_description": page_data["meta_description"],
        "meta_tags": page_data["meta_tags"],
        "content": page_data["content"],
        "embedding": mock_embedding,
    }
    mock_insert.assert_called_once_with(expected_db_data)

def test_process_page_data_task_missing_data():
    # Arrange
    page_data = {"url": "http://example.com"} # Missing content

    # Act & Assert
    # We expect it to log an error and not raise one.
    # We can't easily test the log output here without more setup.
    # So we just run it and expect no exception.
    process_page_data_task(page_data)