import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
import uuid

# It's important to set the environment variable before importing the app
import os
os.environ['TESTING'] = 'True'

from src.main import app

@pytest.fixture(scope="module")
def client():
    """
    Create a test client for the FastAPI app.
    """
    with TestClient(app) as c:
        yield c

@pytest.fixture
def mock_db_functions():
    """
    Mock all database functions to isolate tests from the DB layer.
    """
    with patch('src.main.get_jobs') as mock_get_jobs, \
         patch('src.main.get_job') as mock_get_job, \
         patch('src.main.create_job') as mock_create_job, \
         patch('src.main.update_job') as mock_update_job, \
         patch('src.main.delete_job') as mock_delete_job, \
         patch('src.main.get_web_pages') as mock_get_web_pages, \
         patch('src.main.get_dashboard_analytics') as mock_get_dashboard_analytics, \
         patch('src.main.search') as mock_search:
        
        yield {
            "get_jobs": mock_get_jobs,
            "get_job": mock_get_job,
            "create_job": mock_create_job,
            "update_job": mock_update_job,
            "delete_job": mock_delete_job,
            "get_web_pages": mock_get_web_pages,
            "get_dashboard_analytics": mock_get_dashboard_analytics,
            "search": mock_search
        }

@pytest.fixture
def mock_celery_task():
    """
    Mock the Celery task.
    """
    with patch('src.main.run_crawler_task.delay') as mock_task:
        yield mock_task

def test_list_jobs_api(client, mock_db_functions):
    """
    Test the endpoint for listing jobs.
    """
    mock_jobs = [
        {"id": str(uuid.uuid4()), "status": "completed"},
        {"id": str(uuid.uuid4()), "status": "running"}
    ]
    mock_db_functions['get_jobs'].return_value = mock_jobs

    response = client.get("/api/jobs?limit=10&offset=0")
    
    assert response.status_code == 200
    assert response.json() == mock_jobs
    mock_db_functions['get_jobs'].assert_called_once_with(limit=10, offset=0)

def test_get_job_api_found(client, mock_db_functions):
    """
    Test getting a single job that exists.
    """
    job_id = uuid.uuid4()
    mock_job = {"id": str(job_id), "status": "completed"}
    mock_db_functions['get_job'].return_value = mock_job

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 200
    assert response.json() == mock_job
    mock_db_functions['get_job'].assert_called_once_with(job_id)

def test_get_job_api_not_found(client, mock_db_functions):
    """
    Test getting a single job that does not exist.
    """
    job_id = uuid.uuid4()
    mock_db_functions['get_job'].return_value = None

    response = client.get(f"/api/jobs/{job_id}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Job not found"}

def test_start_crawler_success(client, mock_db_functions, mock_celery_task):
    """
    Test the endpoint for starting a crawler successfully.
    """
    job_id = uuid.uuid4()
    mock_db_functions['create_job'].return_value = {"id": job_id}
    mock_db_functions['update_job'].return_value = True

    request_data = {
        "domain": "example.com",
        "depth": 2,
        "flags": {"some_flag": True}
    }

    response = client.post("/start-crawler", json=request_data)

    assert response.status_code == 202
    data = response.json()
    assert data['status'] == 'queued'
    assert data['domain'] == 'example.com'
    assert data['job_id'] == str(job_id)
    
    mock_db_functions['create_job'].assert_called_once()
    mock_celery_task.assert_called_once_with(str(job_id), "example.com", 2, {"some_flag": True})
    mock_db_functions['update_job'].assert_called_once()



def test_dashboard_analytics_endpoint(client, mock_db_functions):
    """
    Test the dashboard analytics endpoint.
    """
    mock_analytics = {"total_pages": 100, "total_jobs": 5}
    mock_db_functions['get_dashboard_analytics'].return_value = mock_analytics

    response = client.get("/dashboard-analytics")

    assert response.status_code == 200
    assert response.json() == mock_analytics
    mock_db_functions['get_dashboard_analytics'].assert_called_once()

def test_search_api_endpoint(client, mock_db_functions):
    """
    Test the search endpoint.
    """
    mock_results = [{"url": "http://example.com", "title": "Example"}]
    mock_db_functions['search'].return_value = mock_results

    response = client.post("/search", json={"query": "test", "limit": 5})

    assert response.status_code == 200
    assert response.json() == mock_results
    mock_db_functions['search'].assert_called_once_with("test", 5)
