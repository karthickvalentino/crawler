from typing import Dict, Any, Optional
import logging
from datetime import datetime
from src.crawlers.interface import CrawlerInterface, CrawlerStatus
from src.crawlers.scrapy.dynamic_spider import DynamicSpider

logger = logging.getLogger(__name__)


class ScrapyCrawler(CrawlerInterface):
    """Scrapy-based crawler implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.spider_name = config.get('spider_name')
        self.spider_class = config.get('spider_class')
        self.spider_module = config.get('spider_module')
        self.crawler_process = None
        self.crawler_runner = None
        # self.deferred = None
        self._validate_scrapy_config()
    
    def _validate_scrapy_config(self):
        """Validate Scrapy-specific configuration"""
        if not self.spider_name and not self.spider_class:
            raise ValueError("Either spider_name or spider_class must be provided")
    
    def start(self, **kwargs) -> bool:
        """Start the Scrapy spider"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning(f"Crawler {self.name} is already running")
                return False
            
            # Clear any previous errors
            self._clear_error()
            
            # Import Scrapy components
            from scrapy.crawler import CrawlerRunner, CrawlerProcess
            from scrapy.utils.project import get_project_settings
            # from twisted.internet import reactor, defer
            
            # Get Scrapy settings
            settings = get_project_settings()
            
            # Update settings with config
            scrapy_settings = self.config.get('settings', {})
            for key, value in scrapy_settings.items():
                settings.set(key, value)
            
            # Initialize crawler runner if not exists
            if not self.crawler_runner:
                # self.crawler_runner = CrawlerRunner(settings)
                self.crawler_runner = CrawlerProcess(settings)
            
            # Determine spider to run
            spider_to_run = self.spider_class or self.spider_name
            
            # Start the spider
            self.deferred = self.crawler_runner.crawl(DynamicSpider, start_url=settings.get('START_URLS')[0], custom_flags={} ,**kwargs)
            self.crawler_runner.start()
            # Set up completion callback
            self.deferred.addCallback(self._on_spider_completed)
            self.deferred.addErrback(self._on_spider_error)
            
            # Update status and stats
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
            
            if self.crawler_runner:
                self.crawler_runner.stop()
            
            if self.deferred and not self.deferred.called:
                self.deferred.cancel()
            
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
            
            # Note: Scrapy doesn't have built-in pause functionality
            # This would need to be implemented in the spider itself
            # For now, we just change the status
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
            'spider_class': str(self.spider_class) if self.spider_class else None,
            'spider_module': self.spider_module,
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
    
    def configure(self, config: Dict[str, Any]) -> bool:
        """Update crawler configuration"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning("Cannot update configuration while crawler is running")
                return False
            
            # Validate new configuration
            if not self.validate_config(config):
                return False
            
            # Update configuration
            self.config.update(config)
            self.spider_name = config.get('spider_name', self.spider_name)
            self.spider_class = config.get('spider_class', self.spider_class)
            self.spider_module = config.get('spider_module', self.spider_module)
            
            logger.info(f"Updated configuration for crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to update configuration: {str(e)}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Scrapy crawler configuration"""
        try:
            # Check required fields
            spider_name = config.get('spider_name', self.spider_name)
            spider_class = config.get('spider_class', self.spider_class)
            
            if not spider_name and not spider_class:
                self._set_error("Either spider_name or spider_class must be provided")
                return False
            
            # Validate settings if provided
            settings = config.get('settings', {})
            if not isinstance(settings, dict):
                self._set_error("Settings must be a dictionary")
                return False
            
            # Validate spider module if provided
            spider_module = config.get('spider_module')
            if spider_module and not isinstance(spider_module, str):
                self._set_error("Spider module must be a string")
                return False
            
            return True
            
        except Exception as e:
            self._set_error(f"Configuration validation failed: {str(e)}")
            return False
    
    def _on_spider_completed(self, result):
        """Callback when spider completes successfully"""
        self._finalize_stats()
        self.status = CrawlerStatus.COMPLETED
        logger.info(f"Scrapy crawler {self.name} completed successfully")
        return result
    
    def _on_spider_error(self, failure):
        """Callback when spider encounters an error"""
        self._finalize_stats()
        self._set_error(f"Spider failed: {str(failure.value)}")
        logger.error(f"Scrapy crawler {self.name} failed: {failure.value}")
        return failure
    
    def _finalize_stats(self):
        """Finalize crawler statistics"""
        self.stats.end_time = datetime.now()
        if self.stats.start_time:
            self.stats.duration = (self.stats.end_time - self.stats.start_time).total_seconds()
    
    def get_spider_stats(self) -> Dict[str, Any]:
        """Get detailed Scrapy spider statistics"""
        if self.crawler_runner and hasattr(self.crawler_runner, 'crawlers'):
            for crawler in self.crawler_runner.crawlers:
                if crawler.spider.name == self.spider_name:
                    return dict(crawler.stats.get_stats())
        return {}


# Configuration example for Scrapy crawler
SCRAPY_CONFIG_EXAMPLE = {
    'spider_name': 'example_spider',
    'spider_class': None,  # Can be set to actual spider class
    # 'spider_module': 'src.crawlers.scrapy',
    'settings': {
        'ROBOTSTXT_OBEY': True,
        # 'DOWNLOAD_DELAY': 1,
        # 'CONCURRENT_REQUESTS': 16,
        # 'CONCURRENT_REQUESTS_PER_DOMAIN': 8,
        # 'AUTOTHROTTLE_ENABLED': True,
        # 'AUTOTHROTTLE_START_DELAY': 1,
        # 'AUTOTHROTTLE_MAX_DELAY': 60,
        # 'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'USER_AGENT': 'myproject (+http://www.yourdomain.com)',
        # 'ITEM_PIPELINES': {
        #     'myproject.pipelines.ValidationPipeline': 300,
        #     'myproject.pipelines.DatabasePipeline': 400,
        # },
        'EXTENSIONS': {
            'scrapy.extensions.telnet.TelnetConsole': None,
        }
    }
}


def create_scrapy_crawler(name: str, spider_name: str, **kwargs) -> 'ScrapyCrawler':
    """Convenience function to create a Scrapy crawler"""
    config = SCRAPY_CONFIG_EXAMPLE.copy()
    config['spider_name'] = spider_name
    config.update(kwargs)
    return ScrapyCrawler(name, config)