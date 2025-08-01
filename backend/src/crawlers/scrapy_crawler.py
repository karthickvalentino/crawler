import threading
from typing import Dict, Any, Optional
import logging
from datetime import datetime
from src.crawlers.interface import CrawlerInterface, CrawlerStatus
from src.crawlers.scrapy.dynamic_spider import DynamicSpider
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

logger = logging.getLogger(__name__)


class ScrapyCrawler(CrawlerInterface):
    """Scrapy-based crawler implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.spider_name = config.get('spider_name')
        self.start_url = config.get('start_url')
        self.crawler_process = None
    
    def start(self, **kwargs) -> bool:
        """Start the Scrapy spider"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning(f"Crawler {self.name} is already running")
                return False
            
            self._clear_error()
            
            settings = get_project_settings()
            
            scrapy_settings = self.config.get('settings', {})
            for key, value in scrapy_settings.items():
                settings.set(key, value)
            
            self.crawler_process = CrawlerProcess(settings)
            
            self.crawler_process.crawl(DynamicSpider, start_url=self.start_url, custom_flags={} ,**kwargs)
            
            thread = threading.Thread(target=self.crawler_process.start)
            thread.daemon = True
            thread.start()
            
            self.status = CrawlerStatus.RUNNING
            self.stats.start_time = datetime.now()
            
            logger.info(f"Started Scrapy crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to start crawler: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the Scrapy spider"""
        try:
            if self.status not in [CrawlerStatus.RUNNING, CrawlerStatus.PAUSED]:
                logger.info(f"Crawler {self.name} is not running")
                return True
            
            if self.crawler_process:
                self.crawler_process.stop()
            
            self._finalize_stats()
            self.status = CrawlerStatus.STOPPED
            
            logger.info(f"Stopped Scrapy crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to stop crawler: {str(e)}")
            return False
    
    def pause(self) -> bool:
        """Pause the Scrapy spider"""
        try:
            if self.status != CrawlerStatus.RUNNING:
                logger.warning(f"Cannot pause crawler {self.name} - not running")
                return False
            
            self.status = CrawlerStatus.PAUSED
            logger.info(f"Paused Scrapy crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to pause crawler: {str(e)}")
            return False
    
    def resume(self) -> bool:
        """Resume the Scrapy spider"""
        try:
            if self.status != CrawlerStatus.PAUSED:
                logger.warning(f"Cannot resume crawler {self.name} - not paused")
                return False
            
            self.status = CrawlerStatus.RUNNING
            logger.info(f"Resumed Scrapy crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to resume crawler: {str(e)}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Scrapy crawler"""
        return {
            'name': self.name,
            'type': 'scrapy',
            'status': self.status.value,
            'spider_name': self.spider_name,
            'stats': {
                'items_scraped': self.stats.items_scraped,
                'pages_visited': self.stats.pages_visited,
                'errors_count': self.stats.errors_count,
                'start_time': self.stats.start_time.isoformat() if self.stats.start_time else None,
                'end_time': self.stats.end_time.isoformat() if self.stats.end_time else None,
                'duration': self.stats.duration
            },
            'error_message': self._error_message,
            'config': self.config
        }
    
    def _finalize_stats(self):
        """Finalize crawler statistics"""
        self.stats.end_time = datetime.now()
        if self.stats.start_time:
            self.stats.duration = (self.stats.end_time - self.stats.start_time).total_seconds()


def create_scrapy_crawler(name: str, **kwargs) -> 'ScrapyCrawler':
    """Convenience function to create a Scrapy crawler"""
    return ScrapyCrawler(name, kwargs)