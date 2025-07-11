"""
Event handlers for crawler operations
Handles RabbitMQ events and manages crawler lifecycle
"""

import asyncio
import logging
from typing import Dict, Any
from datetime import datetime

from src.rabbitmq_events import (
    CrawlerEvent, 
    publish_crawler_event,
    register_crawler_event_handler
)

from src.crawlers.crawler_factory import (
    create_scrapy_crawler_with_settings,
    create_selenium_crawler_with_options,
    create_and_register_crawler,
    start_crawler_by_name,
    stop_crawler_by_name,
    pause_crawler_by_name,
    resume_crawler_by_name,
    get_crawler_status_by_name,
    get_crawler_manager
)
from src.crawlers.impl import CrawlerFactory
from src.crawlers.interface import CrawlerStatus

logger = logging.getLogger(__name__)

class CrawlerEventHandler:
    """Handles crawler-related events"""
    
    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop
        self.active_crawlers = {}  # Track active crawlers
        
    def run_async(self, coro):
        """Run async function in the event loop"""
        future = asyncio.run_coroutine_threadsafe(coro, self.loop)
        return future.result(timeout=30)
    
    def get_crawler_type_from_env(self) -> str:
        """Get crawler type from environment variable"""
        import os
        crawler_type = os.getenv('CRAWLER_TYPE', 'scrapy').lower()
        supported_types = CrawlerFactory.get_supported_types()
        
        if crawler_type not in supported_types:
            logger.warning(f"Unsupported crawler type '{crawler_type}'. Using 'scrapy'.")
            crawler_type = 'scrapy'
        
        return crawler_type
    
    def create_crawler_from_event_data(self, data: Dict[str, Any]) -> str:
        """Create a crawler from event data"""
        job_id = data.get('job_id')
        url = data.get('url')
        depth = data.get('depth', 1)
        custom_flags = data.get('flags', {})
        crawler_type = data.get('crawler_type') or self.get_crawler_type_from_env()
        
        crawler_name = f"crawler_{job_id}"
        
        try:
            if crawler_type == 'scrapy':
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
                driver_type = custom_flags.get('driver_type', 'chrome')
                options = {
                    'start_url': url,
                    'max_depth': depth,
                    'disable_images': custom_flags.get('disable_images', True),
                    **custom_flags.get('selenium_options', {})
                }
                
                crawler = create_selenium_crawler_with_options(
                    name=crawler_name,
                    driver_type=driver_type,
                    headless=custom_flags.get('headless', True),
                    timeout=custom_flags.get('timeout', 30),
                    custom_options=options,
                    auto_register=True
                )
                
            elif crawler_type == 'api':
                config = {
                    'base_url': url,
                    'endpoints': custom_flags.get('endpoints', ['/']),
                    'rate_limit': custom_flags.get('rate_limit', 1.0),
                    'max_depth': depth,
                    **custom_flags.get('api_config', {})
                }
                
                crawler = create_and_register_crawler(
                    crawler_type='api',
                    name=crawler_name,
                    config=config,
                    auto_start=False
                )
            
            else:
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
                # Store crawler info
                self.active_crawlers[job_id] = {
                    'crawler_name': crawler_name,
                    'crawler_type': crawler_type,
                    'url': url,
                    'depth': depth,
                    'flags': custom_flags,
                    'created_at': datetime.now().isoformat()
                }
                
                logger.info(f"Created {crawler_type} crawler: {crawler_name} for job: {job_id}")
                return crawler_name
            else:
                logger.error(f"Failed to create {crawler_type} crawler for job: {job_id}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating crawler for job {job_id}: {str(e)}")
            return None
    
    def handle_start_crawler(self, data: Dict[str, Any]):
        """Handle start crawler event"""
        try:
            job_id = data.get('job_id')
            logger.info(f"Handling start crawler event for job: {job_id}")
            
            # Create crawler if it doesn't exist
            if job_id not in self.active_crawlers:
                crawler_name = self.create_crawler_from_event_data(data)
                if not crawler_name:
                    # Publish failure event
                    publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                        'job_id': job_id,
                        'error': 'Failed to create crawler',
                        'timestamp': datetime.now().isoformat()
                    })
                    return
            else:
                crawler_name = self.active_crawlers[job_id]['crawler_name']
            
            # Start the crawler
            success = self.run_async(start_crawler_by_name(crawler_name))
            
            if success:
                # Publish success event
                publish_crawler_event(CrawlerEvent.CRAWLER_STARTED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'crawler_type': self.active_crawlers[job_id]['crawler_type'],
                    'url': self.active_crawlers[job_id]['url'],
                    'timestamp': datetime.now().isoformat()
                })
                
                # Start monitoring crawler progress
                self._start_crawler_monitoring(job_id, crawler_name)
                
                logger.info(f"Successfully started crawler: {crawler_name}")
            else:
                # Publish failure event
                publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'error': 'Failed to start crawler',
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"Failed to start crawler: {crawler_name}")
                
        except Exception as e:
            logger.error(f"Error handling start crawler event: {str(e)}")
            publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                'job_id': data.get('job_id'),
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
    
    def handle_stop_crawler(self, data: Dict[str, Any]):
        """Handle stop crawler event"""
        try:
            job_id = data.get('job_id')
            logger.info(f"Handling stop crawler event for job: {job_id}")
            
            if job_id not in self.active_crawlers:
                logger.warning(f"Job {job_id} not found in active crawlers")
                return
            
            crawler_name = self.active_crawlers[job_id]['crawler_name']
            
            # Stop the crawler
            success = self.run_async(stop_crawler_by_name(crawler_name))
            
            if success:
                # Remove from active crawlers
                crawler_info = self.active_crawlers.pop(job_id)
                
                # Publish success event
                publish_crawler_event(CrawlerEvent.CRAWLER_STOPPED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'crawler_type': crawler_info['crawler_type'],
                    'timestamp': datetime.now().isoformat()
                })
                
                logger.info(f"Successfully stopped crawler: {crawler_name}")
            else:
                publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'error': 'Failed to stop crawler',
                    'timestamp': datetime.now().isoformat()
                })
                logger.error(f"Failed to stop crawler: {crawler_name}")
                
        except Exception as e:
            logger.error(f"Error handling stop crawler event: {str(e)}")
    
    def handle_pause_crawler(self, data: Dict[str, Any]):
        """Handle pause crawler event"""
        try:
            job_id = data.get('job_id')
            logger.info(f"Handling pause crawler event for job: {job_id}")
            
            if job_id not in self.active_crawlers:
                logger.warning(f"Job {job_id} not found in active crawlers")
                return
            
            crawler_name = self.active_crawlers[job_id]['crawler_name']
            
            # Pause the crawler
            success = self.run_async(pause_crawler_by_name(crawler_name))
            
            if success:
                publish_crawler_event(CrawlerEvent.CRAWLER_PAUSED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Successfully paused crawler: {crawler_name}")
            else:
                publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'error': 'Failed to pause crawler',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error handling pause crawler event: {str(e)}")
    
    def handle_resume_crawler(self, data: Dict[str, Any]):
        """Handle resume crawler event"""
        try:
            job_id = data.get('job_id')
            logger.info(f"Handling resume crawler event for job: {job_id}")
            
            if job_id not in self.active_crawlers:
                logger.warning(f"Job {job_id} not found in active crawlers")
                return
            
            crawler_name = self.active_crawlers[job_id]['crawler_name']
            
            # Resume the crawler
            success = self.run_async(resume_crawler_by_name(crawler_name))
            
            if success:
                publish_crawler_event(CrawlerEvent.CRAWLER_RESUMED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'timestamp': datetime.now().isoformat()
                })
                logger.info(f"Successfully resumed crawler: {crawler_name}")
            else:
                publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                    'job_id': job_id,
                    'crawler_name': crawler_name,
                    'error': 'Failed to resume crawler',
                    'timestamp': datetime.now().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error handling resume crawler event: {str(e)}")
    
    def _start_crawler_monitoring(self, job_id: str, crawler_name: str):
        """Start monitoring crawler progress and status"""
        def monitor():
            import time
            import threading
            
            def monitor_loop():
                last_status = None
                consecutive_same_status = 0
                
                while job_id in self.active_crawlers:
                    try:
                        # Get current status
                        status = get_crawler_status_by_name(crawler_name)
                        current_status = status.get('status', 'unknown')
                        stats = status.get('stats', {})
                        
                        # Check if status changed
                        if current_status != last_status:
                            # Publish progress event
                            publish_crawler_event(CrawlerEvent.CRAWLER_PROGRESS, {
                                'job_id': job_id,
                                'crawler_name': crawler_name,
                                'status': current_status,
                                'stats': stats,
                                'timestamp': datetime.now().isoformat()
                            })
                            
                            consecutive_same_status = 0
                        else:
                            consecutive_same_status += 1
                        
                        # Check if crawler completed
                        if current_status in ['completed', 'finished', 'done']:
                            # Remove from active crawlers
                            if job_id in self.active_crawlers:
                                crawler_info = self.active_crawlers.pop(job_id)
                                
                                # Publish completion event
                                publish_crawler_event(CrawlerEvent.CRAWLER_COMPLETED, {
                                    'job_id': job_id,
                                    'crawler_name': crawler_name,
                                    'crawler_type': crawler_info['crawler_type'],
                                    'url': crawler_info['url'],
                                    'final_stats': stats,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                logger.info(f"Crawler {crawler_name} completed successfully")
                            break
                        
                        # Check if crawler failed
                        elif current_status in ['failed', 'error', 'stopped'] and consecutive_same_status > 3:
                            # Remove from active crawlers
                            if job_id in self.active_crawlers:
                                crawler_info = self.active_crawlers.pop(job_id)
                                
                                # Publish failure event
                                publish_crawler_event(CrawlerEvent.CRAWLER_FAILED, {
                                    'job_id': job_id,
                                    'crawler_name': crawler_name,
                                    'crawler_type': crawler_info['crawler_type'],
                                    'error': status.get('error_message', 'Crawler failed'),
                                    'final_stats': stats,
                                    'timestamp': datetime.now().isoformat()
                                })
                                
                                logger.error(f"Crawler {crawler_name} failed")
                            break
                        
                        last_status = current_status
                        time.sleep(5)  # Check every 5 seconds
                        
                    except Exception as e:
                        logger.error(f"Error monitoring crawler {crawler_name}: {str(e)}")
                        time.sleep(10)  # Wait longer on error
            
            # Start monitoring in separate thread
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()
        
        monitor()

def setup_crawler_event_handlers(loop: asyncio.AbstractEventLoop):
    """Setup all crawler event handlers"""
    handler = CrawlerEventHandler(loop)
    
    # Register event handlers
    register_crawler_event_handler(CrawlerEvent.START_CRAWLER, handler.handle_start_crawler)
    register_crawler_event_handler(CrawlerEvent.STOP_CRAWLER, handler.handle_stop_crawler)
    register_crawler_event_handler(CrawlerEvent.PAUSE_CRAWLER, handler.handle_pause_crawler)
    register_crawler_event_handler(CrawlerEvent.RESUME_CRAWLER, handler.handle_resume_crawler)
    
    logger.info("Crawler event handlers registered successfully")
    return handler