import asyncio
import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from starlette.middleware.cors import CORSMiddleware

from src.crawlers.crawler_event_handlers import setup_crawler_event_handlers
from src.crawlers.crawler_factory import (
    get_all_crawler_statuses, get_crawler_status_by_name)
from src.data_processing_handlers import setup_data_processing_handlers
from src.db import create_job, delete_job, get_job, get_jobs, update_job
from src.models import JobCreate, JobUpdate
from src.rabbitmq_events import (CrawlerEvent, event_manager,
                                 publish_crawler_event, start_event_system,
                                 stop_event_system)
from src.search import get_dashboard_analytics, get_web_pages, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variable for event handler
event_handler = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    global event_handler
    logger.info("System initializing...")
    
    loop = asyncio.get_event_loop()
    
    # Setup event handlers
    event_handler = setup_crawler_event_handlers(loop)
    setup_data_processing_handlers()
    
    # Start RabbitMQ event system
    if not start_event_system():
        logger.error("Failed to start RabbitMQ event system")
        # In a real-world scenario, you might want to prevent the app from starting
    else:
        logger.info("RabbitMQ event system started successfully")
        
    yield
    
    logger.info("Shutting down application...")
    
    # Stop all running crawlers gracefully
    jobs = get_jobs(limit=1000)
    for job in jobs:
        if job['status'] in ['running', 'queued', 'paused']:
            try:
                event_data = {
                    'job_id': str(job['id']),
                    'requested_at': datetime.now().isoformat()
                }
                publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
            except Exception as e:
                logger.error(f"Error stopping crawler {job['id']} during shutdown: {str(e)}")
                
    # Stop event system
    stop_event_system()
    logger.info("Application shutdown complete")

app = FastAPI(
    title="Crawler Service API",
    description="API for managing web crawlers and searching content.",
    version="1.0.0",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict this to your frontend's domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Exception Handler
@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"error": "Invalid input", "detail": str(exc)},
    )

@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"error": "Internal Server Error", "detail": str(exc)},
    )

# --- API Endpoints ---

@app.get("/dashboard-analytics")
def dashboard_analytics():
    """Get dashboard analytics"""
    return get_dashboard_analytics()

@app.get("/web-pages")
def list_web_pages(
    limit: int = 10,
    offset: int = 0,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    query: Optional[str] = None,
):
    """List web pages with pagination, sorting, and filtering"""
    return get_web_pages(limit, offset, sort_by, sort_order, query)

@app.get("/api/jobs")
def list_jobs_api(limit: int = 100, offset: int = 0):
    """List all crawler jobs"""
    return get_jobs(limit=limit, offset=offset)

@app.get("/api/jobs/{job_id}")
def get_job_api(job_id: uuid.UUID):
    """Get a specific job by ID"""
    job = get_job(job_id)
    if job:
        return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.put("/api/jobs/{job_id}")
def update_job_api(job_id: uuid.UUID, job_update: JobUpdate):
    """Update a job's status or result"""
    job = update_job(job_id, job_update)
    if job:
        return job
    raise HTTPException(status_code=404, detail="Job not found")

@app.delete("/api/jobs/{job_id}")
def delete_job_api(job_id: uuid.UUID):
    """Delete a job"""
    if delete_job(job_id):
        return {"message": "Job deleted successfully"}
    raise HTTPException(status_code=404, detail="Job not found")

class StartCrawlerRequest(BaseModel):
    domain: str
    depth: int = 1
    flags: Dict[str, Any] = {}

@app.post("/start-crawler", status_code=202)
def start_crawler(req: StartCrawlerRequest):
    """Start a crawler by publishing an event to RabbitMQ"""
    job_in = JobCreate(
        parameters={
            "domain": req.domain,
            "depth": req.depth,
            "flags": req.flags,
        }
    )
    job = create_job(job_in)
    job_id = str(job['id'])

    event_data = {
        'job_id': job_id,
        'url': req.domain,
        'depth': req.depth,
        'flags': req.flags,
        'requested_at': datetime.now().isoformat()
    }
    
    success = publish_crawler_event(CrawlerEvent.START_CRAWLER, event_data)
    
    if success:
        logger.info(f"Published start crawler event for job: {job_id}")
        update_job(uuid.UUID(job_id), JobUpdate(status='queued'))
        return {
            "status": "queued",
            "job_id": job_id,
            "domain": req.domain,
            "depth": req.depth,
            "message": "Crawler job queued successfully"
        }
    else:
        update_job(uuid.UUID(job_id), JobUpdate(status='failed'))
        raise HTTPException(status_code=500, detail="Failed to queue crawler job")

@app.post("/stop-crawler/{job_id}")
def stop_crawler_by_job(job_id: uuid.UUID):
    """Stop a specific crawler by publishing a stop event"""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    event_data = {
        'job_id': str(job_id),
        'requested_at': datetime.now().isoformat()
    }
    
    success = publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
    
    if success:
        update_job(job_id, JobUpdate(status='stopping'))
        logger.info(f"Published stop crawler event for job: {job_id}")
        return {
            "status": "stopping",
            "job_id": str(job_id),
            "message": "Stop command sent successfully"
        }
    else:
        raise HTTPException(status_code=500, detail=f"Failed to send stop command for job {job_id}")

@app.post("/stop-crawlers")
def stop_all_crawlers_api():
    """Stop all running crawlers by publishing stop events for each"""
    stopped_jobs = []
    failed_jobs = []
    
    jobs = get_jobs(limit=1000)
    for job in jobs:
        if job['status'] in ['running', 'queued', 'paused']:
            event_data = {
                'job_id': str(job['id']),
                'requested_at': datetime.now().isoformat()
            }
            
            success = publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
            
            if success:
                update_job(job['id'], JobUpdate(status='stopping'))
                stopped_jobs.append(str(job['id']))
            else:
                failed_jobs.append(str(job['id']))
    
    return {
        "status": "stopping",
        "message": f"Stop commands sent for {len(stopped_jobs)} crawlers",
        "stopped_jobs": stopped_jobs,
        "failed_jobs": failed_jobs,
    }

@app.get("/crawler-status/{job_id}")
def get_crawler_status(job_id: uuid.UUID):
    """Get the status of a specific crawler"""
    job_info = get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    
    detailed_status = {}
    job_id_str = str(job_id)
    if event_handler and job_id_str in event_handler.active_crawlers:
        crawler_name = event_handler.active_crawlers[job_id_str]['crawler_name']
        try:
            detailed_status = get_crawler_status_by_name(crawler_name)
        except Exception as e:
            logger.warning(f"Could not get detailed status for {crawler_name}: {str(e)}")
    
    job_info['detailed_status'] = detailed_status.get('status', 'unknown')
    job_info['stats'] = detailed_status.get('stats', {})
    job_info['error_message'] = detailed_status.get('error_message')
    
    return job_info

@app.get("/crawlers-status")
def get_all_crawlers_status_api():
    """Get the status of all crawlers"""
    jobs = get_jobs(limit=1000)
    formatted_statuses = {}
    
    for job in jobs:
        job_id = str(job['id'])
        detailed_status = {}
        if event_handler and job_id in event_handler.active_crawlers:
            crawler_name = event_handler.active_crawlers[job_id]['crawler_name']
            try:
                detailed_status = get_crawler_status_by_name(crawler_name)
            except Exception as e:
                logger.warning(f"Could not get detailed status for {crawler_name}: {str(e)}")
        
        job['detailed_status'] = detailed_status.get('status', 'unknown')
        job['stats'] = detailed_status.get('stats', {})
        formatted_statuses[job_id] = job

    return {
        "total_jobs": len(jobs),
        "crawlers": formatted_statuses,
        "rabbitmq_connected": event_manager.consumer_connection and event_manager.consumer_connection.is_open,
        "timestamp": datetime.now().isoformat()
    }

class SearchRequest(BaseModel):
    query: str
    limit: int = 5

@app.post("/search")
def search_api(req: SearchRequest):
    """Search endpoint"""
    results = search(req.query, req.limit)
    return results

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "src.main:app",
        host=os.getenv('FLASK_HOST', '0.0.0.0'),
        port=int(os.getenv('FLASK_PORT', '5000')),
        reload=True
    )
