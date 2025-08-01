import asyncio
import logging
import os
import threading
import uuid
from datetime import datetime
from multiprocessing import Process
from typing import Any, Dict, Optional

from flask import Flask, jsonify, request
from flask_cors import CORS
from src.crawlers.crawler_event_handlers import setup_crawler_event_handlers

# Import our new crawler system
from src.crawlers.crawler_factory import (
    create_and_register_crawler,
    get_all_crawler_statuses,
    get_crawler_manager,
    get_crawler_status_by_name,
    start_crawler_by_name,
    stop_all_crawlers,
    stop_crawler_by_name,
)
from src.data_processing_handlers import setup_data_processing_handlers
from src.db import create_job, delete_job, get_job, get_jobs, update_job
from src.models import JobCreate, JobUpdate

# Import RabbitMQ event system
from src.rabbitmq_events import (
    CrawlerEvent,
    event_manager,
    publish_crawler_event,
    start_event_system,
    stop_event_system,
)
from src.search import get_dashboard_analytics, get_web_pages, search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables for async support
loop = None
loop_thread = None
event_handler = None

def run_async(coro):
    """Run async function in the event loop"""
    print('start process')
    p = Process(target=coro)
    p.start()

def setup_event_loop():
    """Setup event loop in a separate thread for async operations"""
    global loop, loop_thread
    
    def run_loop():
        global loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_forever()
    
    loop_thread = threading.Thread(target=run_loop, daemon=True)
    loop_thread.start()
    
    # Wait for loop to be ready
    import time
    while loop is None:
        time.sleep(0.1)

def initialize_system():
    """Initialize the complete system"""
    global event_handler
    
    try:
        # Setup event loop
        setup_event_loop()
        
        # Setup event handlers
        event_handler = setup_crawler_event_handlers(loop)
        setup_data_processing_handlers()
        
        # Start RabbitMQ event system
        if not start_event_system():
            logger.error("Failed to start RabbitMQ event system")
            return False
        
        logger.info("System initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize system: {str(e)}")
        return False

@app.route("/dashboard-analytics", methods=["GET"])
def dashboard_analytics():
    """Get dashboard analytics"""
    try:
        analytics = get_dashboard_analytics()
        return jsonify(analytics), 200
    except Exception as e:
        logger.error(f"Error in dashboard_analytics endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/web-pages", methods=["GET"])
def list_web_pages():
    """List web pages with pagination, sorting, and filtering"""
    try:
        limit = int(request.args.get("limit", 10))
        offset = int(request.args.get("offset", 0))
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        query = request.args.get("query")

        result = get_web_pages(limit, offset, sort_by, sort_order, query)
        return jsonify(result), 200
    except Exception as e:
        logger.error(f"Error in list_web_pages endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/api/jobs", methods=["GET"])
def list_jobs_api():
    """List all crawler jobs"""
    limit = int(request.args.get("limit", 100))
    offset = int(request.args.get("offset", 0))
    jobs = get_jobs(limit=limit, offset=offset)
    return jsonify(jobs)

@app.route("/api/jobs/<job_id>", methods=["GET"])
def get_job_api(job_id: str):
    """Get a specific job by ID"""
    try:
        job = get_job(uuid.UUID(job_id))
        if job:
            return jsonify(job)
        return jsonify({"error": "Job not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid job ID format"}), 400

@app.route("/api/jobs/<job_id>", methods=["PUT"])
def update_job_api(job_id: str):
    """Update a job's status or result"""
    try:
        job_update = JobUpdate.parse_obj(request.json)
        job = update_job(uuid.UUID(job_id), job_update)
        if job:
            return jsonify(job)
        return jsonify({"error": "Job not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid job ID format"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route("/api/jobs/<job_id>", methods=["DELETE"])
def delete_job_api(job_id: str):
    """Delete a job"""
    try:
        if delete_job(uuid.UUID(job_id)):
            return jsonify({"message": "Job deleted successfully"})
        return jsonify({"error": "Job not found"}), 404
    except ValueError:
        return jsonify({"error": "Invalid job ID format"}), 400

@app.route("/start-crawler", methods=["POST"])
def start_crawler():
    """Start a crawler by publishing event to RabbitMQ"""
    try:
        data = request.json
        domain = data.get("domain")
        depth = int(data.get("depth", 1))
        custom_flags = data.get("flags", {})
        crawler_type = "scrapy"

        if not domain:
            return jsonify({"error": "Domain is required"}), 400
        
        if depth < 1:
            return jsonify({"error": "Depth must be at least 1"}), 400
        
        job_in = JobCreate(
            job_type=crawler_type,
            parameters={
                "domain": domain,
                "depth": depth,
                "flags": custom_flags,
            }
        )
        job = create_job(job_in)
        job_id = str(job['id'])

        event_data = {
            'job_id': job_id,
            'url': f"{domain}",
            'depth': depth,
            'flags': custom_flags,
            'crawler_type': crawler_type,
            'requested_at': datetime.now().isoformat()
        }
        
        success = publish_crawler_event(CrawlerEvent.START_CRAWLER, event_data)
        
        if success:
            logger.info(f"Published start crawler event for job: {job_id}")
            update_job(uuid.UUID(job_id), JobUpdate(status='queued'))
            return jsonify({
                "status": "queued",
                "job_id": job_id,
                "crawler_type": crawler_type,
                "domain": domain,
                "depth": depth,
                "message": f"Crawler job queued successfully with {crawler_type} engine"
            }), 202
        else:
            update_job(uuid.UUID(job_id), JobUpdate(status='failed'))
            return jsonify({
                "error": "Failed to queue crawler job",
                "job_id": job_id
            }), 500
    
    except Exception as e:
        logger.error(f"Error in start_crawler endpoint: {str(e)}")
        return jsonify({"error": f"Internal server error: {str(e)}"}), 500

@app.route("/stop-crawler/<job_id>", methods=["POST"])
def stop_crawler_by_job(job_id: str):
    """Stop a specific crawler by publishing stop event"""
    try:
        job = get_job(uuid.UUID(job_id))
        if not job:
            return jsonify({"error": f"Job {job_id} not found"}), 404
        
        event_data = {
            'job_id': job_id,
            'requested_at': datetime.now().isoformat()
        }
        
        success = publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
        
        if success:
            update_job(uuid.UUID(job_id), JobUpdate(status='stopping'))
            logger.info(f"Published stop crawler event for job: {job_id}")
            return jsonify({
                "status": "stopping",
                "job_id": job_id,
                "message": "Stop command sent successfully"
            }), 200
        else:
            return jsonify({
                "error": f"Failed to send stop command for job {job_id}",
                "job_id": job_id
            }), 500
    
    except Exception as e:
        logger.error(f"Error stopping crawler for job {job_id}: {str(e)}")
        return jsonify({"error": f"Failed to stop crawler: {str(e)}"}), 500

@app.route("/stop-crawlers", methods=["POST"])
def stop_all_crawlers_api():
    """Stop all running crawlers by publishing stop events for each"""
    try:
        stopped_jobs = []
        failed_jobs = []
        
        jobs = get_jobs(limit=1000) # Assuming not more than 1000 active jobs
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
        
        return jsonify({
            "status": "stopping",
            "message": f"Stop commands sent for {len(stopped_jobs)} crawlers",
            "stopped_jobs": stopped_jobs,
            "failed_jobs": failed_jobs,
        }), 200
    
    except Exception as e:
        logger.error(f"Error stopping all crawlers: {str(e)}")
        return jsonify({"error": f"Failed to stop crawlers: {str(e)}"}), 500

@app.route("/crawler-status/<job_id>", methods=["GET"])
def get_crawler_status(job_id: str):
    """Get status of a specific crawler"""
    try:
        job_info = get_job(uuid.UUID(job_id))
        if not job_info:
            return jsonify({"error": f"Job {job_id} not found"}), 404
        
        detailed_status = {}
        if event_handler and job_id in event_handler.active_crawlers:
            crawler_name = event_handler.active_crawlers[job_id]['crawler_name']
            try:
                detailed_status = get_crawler_status_by_name(crawler_name)
            except Exception as e:
                logger.warning(f"Could not get detailed status for {crawler_name}: {str(e)}")
        
        job_info['detailed_status'] = detailed_status.get('status', 'unknown')
        job_info['stats'] = detailed_status.get('stats', {})
        job_info['error_message'] = detailed_status.get('error_message')
        
        return jsonify(job_info), 200
    
    except Exception as e:
        logger.error(f"Error getting status for job {job_id}: {str(e)}")
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500

@app.route("/crawlers-status", methods=["GET"])
def get_all_crawlers_status():
    """Get status of all crawlers"""
    try:
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

        return jsonify({
            "total_jobs": len(jobs),
            "crawler_type": "scrapy",
            "crawlers": formatted_statuses,
            "rabbitmq_connected": event_manager.consumer_connection and event_manager.consumer_connection.is_open,
            "timestamp": datetime.now().isoformat()
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting all crawler statuses: {str(e)}")
        return jsonify({"error": f"Failed to get statuses: {str(e)}"}), 500

@app.route("/search", methods=["POST"])
def search_api():
    """Search endpoint (unchanged from original)"""
    data = request.json
    query = data.get("query")
    top_k = int(data.get("limit", 5))
    if not query:
        return jsonify({"error": "Query is required"}), 400
    results = search(query, top_k)
    return jsonify(results), 200

# Event status update handlers (called by RabbitMQ events)
def update_job_status_from_event(job_id: str, status: str, additional_data: Dict[str, Any] = None):
    """Update job status from RabbitMQ events"""
    try:
        job_update = JobUpdate(status=status)
        if additional_data:
            job_update.result = additional_data
        update_job(uuid.UUID(job_id), job_update)
        logger.info(f"Updated job {job_id} status to: {status}")
    except Exception as e:
        logger.error(f"Failed to update job {job_id} from event: {e}")

# Register status update handlers with RabbitMQ events
def setup_status_update_handlers():
    """Setup handlers to update job status from RabbitMQ events"""
    from src.rabbitmq_events import register_crawler_event_handler
    
    def handle_crawler_started(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_id, 'running', {
                'crawler_name': data.get('crawler_name'),
                'started_at': data.get('timestamp')
            })
    
    def handle_crawler_stopped(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_id, 'stopped', {
                'stopped_at': data.get('timestamp')
            })
    
    def handle_crawler_completed(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_id, 'completed', {
                'completed_at': data.get('timestamp'),
                'final_stats': data.get('final_stats', {})
            })
    
    def handle_crawler_failed(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_id, 'failed', {
                'failed_at': data.get('timestamp'),
                'error': data.get('error'),
                'final_stats': data.get('final_stats', {})
            })
    
    def handle_crawler_paused(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_id, 'paused', {
                'paused_at': data.get('timestamp')
            })
    
    def handle_crawler_resumed(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_.id, 'running', {
                'resumed_at': data.get('timestamp')
            })
    
    def handle_crawler_progress(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status_from_event(job_id, data.get('status', 'running'), {
                'last_progress_update': data.get('timestamp'),
                'current_stats': data.get('stats', {})
            })
    
    # Register all status update handlers
    register_crawler_event_handler(CrawlerEvent.CRAWLER_STARTED, handle_crawler_started)
    register_crawler_event_handler(CrawlerEvent.CRAWLER_STOPPED, handle_crawler_stopped)
    register_crawler_event_handler(CrawlerEvent.CRAWLER_COMPLETED, handle_crawler_completed)
    register_crawler_event_handler(CrawlerEvent.CRAWLER_FAILED, handle_crawler_failed)
    register_crawler_event_handler(CrawlerEvent.CRAWLER_PAUSED, handle_crawler_paused)
    register_crawler_event_handler(CrawlerEvent.CRAWLER_RESUMED, handle_crawler_resumed)
    register_crawler_event_handler(CrawlerEvent.CRAWLER_PROGRESS, handle_crawler_progress)
    
    logger.info("Status update handlers registered successfully")

# Cleanup function for graceful shutdown
def cleanup_on_shutdown():
    """Cleanup resources on application shutdown"""
    try:
        logger.info("Shutting down application...")
        
        # Stop all running crawlers
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
        
        # Stop event loop
        if loop and loop.is_running():
            loop.call_soon_threadsafe(loop.stop)
        
        logger.info("Application shutdown complete")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}")

# Register cleanup function
import atexit

print("__name__", __name__)

if __name__ == "__main__" or __name__ == "src.app":
    # Initialize system on startup
    if not initialize_system():
        logger.error("Failed to initialize system. Exiting...")
        exit(1)

    # Setup status update handlers
    setup_status_update_handlers()
    
    atexit.register(cleanup_on_shutdown)
    
    # Log startup information
    logger.info(f"Starting Flask app with crawler type: scrapy")
    logger.info(f"RabbitMQ host: {event_manager.host}:{event_manager.port}")
    
    try:
        app.run(
            debug=os.getenv('FLASK_DEBUG', 'False').lower() == 'true',
            host=os.getenv('FLASK_HOST', '0.0.0.0'),
            port=int(os.getenv('FLASK_PORT', '5000'))
        )
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        cleanup_on_shutdown()
    except Exception as e:
        logger.error(f"Error running Flask app: {str(e)}")
        cleanup_on_shutdown()
        raise