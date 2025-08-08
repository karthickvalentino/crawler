import logging
import os
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from src.db import create_job, delete_job, get_job, get_jobs, update_job
from src.models import JobCreate, JobUpdate
from src.search import get_dashboard_analytics, get_web_pages, search
from src.tasks import run_crawler_task
from starlette.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

from src.instrumentation import instrument_application


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Handles startup and shutdown events for the FastAPI application.
    """
    instrument_application(app)
    logger.info("System initializing...")
    yield
    logger.info("Application shutdown complete")


app = FastAPI(
    title="Crawler Service API",
    description="API for managing web crawlers and searching content.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
    """Start a crawler by dispatching a Celery task."""
    job_in = JobCreate(
        parameters={
            "domain": req.domain,
            "depth": req.depth,
            "flags": req.flags,
        }
    )
    job = create_job(job_in)
    job_id = str(job["id"])

    run_crawler_task.delay(job_id, req.domain, req.depth, req.flags)

    logger.info(f"Dispatched crawler task for job: {job_id}")
    update_job(uuid.UUID(job_id), JobUpdate(status="queued"))

    return {
        "status": "queued",
        "job_id": job_id,
        "domain": req.domain,
        "depth": req.depth,
        "message": "Crawler job queued successfully",
    }


@app.get("/crawler-status/{job_id}")
def get_crawler_status(job_id: uuid.UUID):
    """Get the status of a specific crawler from the database."""
    job_info = get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")
    return job_info


@app.get("/crawlers-status")
def get_all_crawlers_status_api():
    """Get the status of all crawlers from the database."""
    jobs = get_jobs(limit=1000)
    return {
        "total_jobs": len(jobs),
        "crawlers": jobs,
        "timestamp": datetime.now().isoformat(),
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

    logging.info("FastAPI application starting...")

    uvicorn.run(
        "src.main:app",
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
        port=int(os.getenv("FLASK_PORT", "5000")),
        reload=True,
    )

    logging.info("FastAPI application started successfully.")
