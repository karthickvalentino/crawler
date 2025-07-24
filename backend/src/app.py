from flask import Flask, request, jsonify
import os
import uuid
import asyncio
import threading
import logging
from typing import Dict, Any, Optional
from multiprocessing import Process
from datetime import datetime

# Import RabbitMQ event system
from src.rabbitmq_events import (
    CrawlerEvent,
    publish_crawler_event,
    start_event_system,
    stop_event_system,
    event_manager
)
from src.crawlers.crawler_event_handlers import setup_crawler_event_handlers
from src.data_processing_handlers import setup_data_processing_handlers

# Import our new crawler system
from src.crawlers.crawler_factory import (
    create_scrapy_crawler_with_settings,
    create_selenium_crawler_with_options,
    create_and_register_crawler,
    start_crawler_by_name,
    stop_crawler_by_name,
    get_crawler_status_by_name,
    get_all_crawler_statuses,
    stop_all_crawlers,
    get_crawler_manager
)
from src.crawlers.impl import CrawlerFactory
from src.crawlers.implementations.custom_example import register_api_crawler
from src.search import search

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Global variables for async support
loop = None
loop_thread = None
running_jobs = {}  # Track running crawler jobs
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
        # Initialize crawler system
        register_api_crawler()
        
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

def get_crawler_type_from_env() -> str:
    """Get crawler type from environment variable"""
    crawler_type = os.getenv('CRAWLER_TYPE', 'scrapy').lower()
    supported_types = CrawlerFactory.get_supported_types()
    
    if crawler_type not in supported_types:
        logger.warning(f"Unsupported crawler type '{crawler_type}' in CRAWLER_TYPE. Using 'scrapy' as default.")
        crawler_type = 'scrapy'
    
    logger.info(f"Using crawler type: {crawler_type}")
    return crawler_type

def create_crawler_from_request(job_id: str, url: str, depth: int, custom_flags: Dict[str, Any]) -> Optional[str]:
    """Create a crawler based on environment configuration and request parameters"""
    crawler_type = get_crawler_type_from_env()
    crawler_name = f"crawler_{job_id}"
    
    try:
        if crawler_type == 'scrapy':
            # Create Scrapy crawler
            spider_name = custom_flags.get('spider_name', 'default_spider')
            settings = {
                'DEPTH_LIMIT': depth,
                'START_URLS': [url],
                'DOWNLOAD_DELAY': custom_flags.get('download_delay', 1),
                'CONCURRENT_REQUESTS': custom_flags.get('concurrent_requests', 8),
                'ROBOTSTXT_OBEY': custom_flags.get('obey_robots', True),
                **custom_flags.get('scrapy_settings', {})
            }
            
            crawler = create_scrapy_crawler_with_settings(
                name=crawler_name,
                spider_name=spider_name,
                custom_settings=settings,
                spider_module=custom_flags.get('spider_module'),
                auto_register=True
            )
            
        elif crawler_type == 'selenium':
            # Create Selenium crawler
            driver_type = custom_flags.get('driver_type', 'chrome')
            options = {
                'start_url': url,
                'max_depth': depth,
                'disable_images': custom_flags.get('disable_images', True),
                'disable_javascript': custom_flags.get('disable_javascript', False),
                **custom_flags.get('selenium_options', {})
            }
            
            crawler = create_selenium_crawler_with_options(
                name=crawler_name,
                driver_type=driver_type,
                headless=custom_flags.get('headless', True),
                timeout=custom_flags.get('timeout', 30),
                window_size=custom_flags.get('window_size'),
                user_agent=custom_flags.get('user_agent'),
                custom_options=options,
                auto_register=True
            )
            
        elif crawler_type == 'api':
            # Create API crawler
            config = {
                'base_url': url,
                'endpoints': custom_flags.get('endpoints', ['/']),
                'rate_limit': custom_flags.get('rate_limit', 1.0),
                'max_depth': depth,
                'timeout': custom_flags.get('timeout', 30),
                'headers': custom_flags.get('headers', {}),
                **custom_flags.get('api_config', {})
            }
            
            crawler = create_and_register_crawler(
                crawler_type='api',
                name=crawler_name,
                config=config,
                auto_start=False
            )
            
        else:
            # Generic crawler creation for custom types
            config = {
                'url': url,
                'depth': depth,
                **custom_flags
            }
            
            crawler = create_and_register_crawler(
                crawler_type=crawler_type,
                name=crawler_name,
                config=config,
                auto_start=False
            )
        
        if crawler:
            logger.info(f"Created {crawler_type} crawler: {crawler_name}")
            return crawler_name, crawler
        else:
            logger.error(f"Failed to create {crawler_type} crawler")
            return None
            
    except Exception as e:
        logger.error(f"Error creating {crawler_type} crawler: {str(e)}")
        return None

@app.route("/start-crawler", methods=["POST"])
def start_crawler():
    """Start a crawler by publishing event to RabbitMQ"""
    try:
        data = request.json
        url = data.get("url")
        depth = int(data.get("depth", 1))
        custom_flags = data.get("flags", {})
        crawler_type = data.get("crawler_type") or get_crawler_type_from_env()

        if not url:
            return jsonify({"error": "URL is required"}), 400
        
        # Validate depth
        if depth < 1:
            return jsonify({"error": "Depth must be at least 1"}), 400
        
        job_id = str(uuid.uuid4())
        
        # Store job metadata
        running_jobs[job_id] = {
            'url': url,
            'depth': depth,
            'flags': custom_flags,
            'crawler_type': crawler_type,
            'status': 'queued',
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }

        # Publish start crawler event to RabbitMQ
        event_data = {
            'job_id': job_id,
            'url': url,
            'depth': depth,
            'flags': custom_flags,
            'crawler_type': crawler_type,
            'requested_at': datetime.now().isoformat()
        }
        
        success = publish_crawler_event(CrawlerEvent.START_CRAWLER, event_data)
        
        if success:
            logger.info(f"Published start crawler event for job: {job_id}")
            return jsonify({
                "status": "queued",
                "job_id": job_id,
                "crawler_type": crawler_type,
                "url": url,
                "depth": depth,
                "message": f"Crawler job queued successfully with {crawler_type} engine"
            }), 202
        else:
            # Remove from running jobs if event publishing failed
            running_jobs.pop(job_id, None)
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
        if job_id not in running_jobs:
            return jsonify({"error": f"Job {job_id} not found"}), 404
        
        # Publish stop crawler event
        event_data = {
            'job_id': job_id,
            'requested_at': datetime.now().isoformat()
        }
        
        success = publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
        
        if success:
            # Update job status
            running_jobs[job_id]['status'] = 'stopping'
            running_jobs[job_id]['updated_at'] = datetime.now().isoformat()
            
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
def stop_all_crawlers():
    """Stop all running crawlers by publishing stop events for each"""
    try:
        stopped_jobs = []
        failed_jobs = []
        
        for job_id in list(running_jobs.keys()):
            event_data = {
                'job_id': job_id,
                'requested_at': datetime.now().isoformat()
            }
            
            success = publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
            
            if success:
                running_jobs[job_id]['status'] = 'stopping'
                running_jobs[job_id]['updated_at'] = datetime.now().isoformat()
                stopped_jobs.append(job_id)
            else:
                failed_jobs.append(job_id)
        
        return jsonify({
            "status": "stopping",
            "message": f"Stop commands sent for {len(stopped_jobs)} crawlers",
            "stopped_jobs": stopped_jobs,
            "failed_jobs": failed_jobs,
            "total_jobs": len(running_jobs)
        }), 200
    
    except Exception as e:
        logger.error(f"Error stopping all crawlers: {str(e)}")
        return jsonify({"error": f"Failed to stop crawlers: {str(e)}"}), 500

@app.route("/crawler-status/<job_id>", methods=["GET"])
def get_crawler_status(job_id: str):
    """Get status of a specific crawler"""
    try:
        if job_id not in running_jobs:
            return jsonify({"error": f"Job {job_id} not found"}), 404
        
        job_info = running_jobs[job_id]
        
        # Try to get detailed status from crawler system if available
        detailed_status = {}
        if event_handler and job_id in event_handler.active_crawlers:
            crawler_name = event_handler.active_crawlers[job_id]['crawler_name']
            try:
                detailed_status = get_crawler_status_by_name(crawler_name)
            except Exception as e:
                logger.warning(f"Could not get detailed status for {crawler_name}: {str(e)}")
        
        return jsonify({
            "job_id": job_id,
            "status": job_info['status'],
            "crawler_type": job_info['crawler_type'],
            "url": job_info['url'],
            "depth": job_info['depth'],
            "flags": job_info['flags'],
            "created_at": job_info['created_at'],
            "updated_at": job_info['updated_at'],
            "detailed_status": detailed_status.get('status', 'unknown'),
            "stats": detailed_status.get('stats', {}),
            "error_message": detailed_status.get('error_message')
        }), 200
    
    except Exception as e:
        logger.error(f"Error getting status for job {job_id}: {str(e)}")
        return jsonify({"error": f"Failed to get status: {str(e)}"}), 500

@app.route("/crawlers-status", methods=["GET"])
def get_all_crawlers_status():
    """Get status of all crawlers"""
    try:
        formatted_statuses = {}
        
        for job_id, job_info in running_jobs.items():
            # Try to get detailed status
            detailed_status = {}
            if event_handler and job_id in event_handler.active_crawlers:
                crawler_name = event_handler.active_crawlers[job_id]['crawler_name']
                try:
                    detailed_status = get_crawler_status_by_name(crawler_name)
                except Exception as e:
                    logger.warning(f"Could not get detailed status for {crawler_name}: {str(e)}")
            
            formatted_statuses[job_id] = {
                "job_id": job_id,
                "status": job_info['status'],
                "crawler_type": job_info['crawler_type'],
                "url": job_info['url'],
                "depth": job_info['depth'],
                "created_at": job_info['created_at'],
                "updated_at": job_info['updated_at'],
                "detailed_status": detailed_status.get('status', 'unknown'),
                "stats": detailed_status.get('stats', {})
            }
        
        return jsonify({
            "total_jobs": len(running_jobs),
            "crawler_type": get_crawler_type_from_env(),
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

@app.route("/config", methods=["GET"])
def get_config():
    """Get current crawler configuration"""
    return jsonify({
        "crawler_type": get_crawler_type_from_env(),
        "supported_types": CrawlerFactory.get_supported_types(),
        "active_jobs": len(running_jobs),
        "environment_variables": {
            "CRAWLER_TYPE": os.getenv('CRAWLER_TYPE', 'scrapy')
        }
    }), 200

# Event status update handlers (called by RabbitMQ events)
def update_job_status(job_id: str, status: str, additional_data: Dict[str, Any] = None):
    """Update job status from RabbitMQ events"""
    if job_id in running_jobs:
        running_jobs[job_id]['status'] = status
        running_jobs[job_id]['updated_at'] = datetime.now().isoformat()
        
        if additional_data:
            running_jobs[job_id].update(additional_data)
        
        logger.info(f"Updated job {job_id} status to: {status}")

# Register status update handlers with RabbitMQ events
def setup_status_update_handlers():
    """Setup handlers to update job status from RabbitMQ events"""
    from src.rabbitmq_events import register_crawler_event_handler
    
    def handle_crawler_started(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, 'running', {
                'crawler_name': data.get('crawler_name'),
                'started_at': data.get('timestamp')
            })
    
    def handle_crawler_stopped(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, 'stopped', {
                'stopped_at': data.get('timestamp')
            })
            # Remove from running jobs after a delay
            def cleanup():
                import time
                time.sleep(60)  # Keep for 1 minute for status queries
                running_jobs.pop(job_id, None)
            
            threading.Thread(target=cleanup, daemon=True).start()
    
    def handle_crawler_completed(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, 'completed', {
                'completed_at': data.get('timestamp'),
                'final_stats': data.get('final_stats', {})
            })
            # Remove from running jobs after a delay
            def cleanup():
                import time
                time.sleep(300)  # Keep for 5 minutes for status queries
                running_jobs.pop(job_id, None)
            
            threading.Thread(target=cleanup, daemon=True).start()
    
    def handle_crawler_failed(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, 'failed', {
                'failed_at': data.get('timestamp'),
                'error': data.get('error'),
                'final_stats': data.get('final_stats', {})
            })
            # Remove from running jobs after a delay
            def cleanup():
                import time
                time.sleep(300)  # Keep for 5 minutes for status queries
                running_jobs.pop(job_id, None)
            
            threading.Thread(target=cleanup, daemon=True).start()
    
    def handle_crawler_paused(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, 'paused', {
                'paused_at': data.get('timestamp')
            })
    
    def handle_crawler_resumed(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, 'running', {
                'resumed_at': data.get('timestamp')
            })
    
    def handle_crawler_progress(data):
        job_id = data.get('job_id')
        if job_id:
            update_job_status(job_id, data.get('status', 'running'), {
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
        for job_id in list(running_jobs.keys()):
            try:
                event_data = {
                    'job_id': job_id,
                    'requested_at': datetime.now().isoformat()
                }
                publish_crawler_event(CrawlerEvent.STOP_CRAWLER, event_data)
            except Exception as e:
                logger.error(f"Error stopping crawler {job_id} during shutdown: {str(e)}")
        
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
atexit.register(cleanup_on_shutdown)

# Initialize system on startup
if not initialize_system():
    logger.error("Failed to initialize system. Exiting...")
    exit(1)

# Setup status update handlers
setup_status_update_handlers()

if __name__ == "__main__":
    # Log startup information
    logger.info(f"Starting Flask app with crawler type: {get_crawler_type_from_env()}")
    logger.info(f"Supported crawler types: {CrawlerFactory.get_supported_types()}")
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
