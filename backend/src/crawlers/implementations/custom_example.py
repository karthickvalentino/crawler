"""
Example of how to create a custom crawler implementation
"""

from typing import Dict, Any
import logging
from datetime import datetime
# import asyncio
from src.crawlers.interface import CrawlerInterface, CrawlerStatus

logger = logging.getLogger(__name__)


class CustomAPICrawler(CrawlerInterface):
    """
    Example custom crawler that fetches data from REST APIs
    This demonstrates how to extend the crawler system
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.base_url = config.get('base_url')
        self.api_key = config.get('api_key')
        self.endpoints = config.get('endpoints', [])
        self.rate_limit = config.get('rate_limit', 1.0)  # seconds between requests
        self.session = None
        self._running = False
    
    def start(self, **kwargs) -> bool:
        """Start the API crawler"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning(f"Crawler {self.name} is already running")
                return False
            
            self._clear_error()
            
            # Import aiohttp for HTTP requests
            import aiohttp
            
            # Create HTTP session
            headers = {}
            if self.api_key:
                headers['Authorization'] = f'Bearer {self.api_key}'
            
            self.session = aiohttp.ClientSession(headers=headers)
            
            self.status = CrawlerStatus.RUNNING
            self.stats.start_time = datetime.now()
            self._running = True
            
            # Start crawling task
            # asyncio.create_task(self._crawl_endpoints())
            
            logger.info(f"Started API crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to start API crawler: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the API crawler"""
        try:
            self._running = False
            
            if self.session:
                self.session.close()
                self.session = None
            
            self._finalize_stats()
            self.status = CrawlerStatus.STOPPED
            
            logger.info(f"Stopped API crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to stop API crawler: {str(e)}")
            return False
    
    def pause(self) -> bool:
        """Pause the API crawler"""
        if self.status != CrawlerStatus.RUNNING:
            return False
        
        self.status = CrawlerStatus.PAUSED
        logger.info(f"Paused API crawler: {self.name}")
        return True
    
    def resume(self) -> bool:
        """Resume the API crawler"""
        if self.status != CrawlerStatus.PAUSED:
            return False
        
        self.status = CrawlerStatus.RUNNING
        logger.info(f"Resumed API crawler: {self.name}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the API crawler"""
        return {
            'name': self.name,
            'type': 'api',
            'status': self.status.value,
            'base_url': self.base_url,
            'endpoints_count': len(self.endpoints),
            'rate_limit': self.rate_limit,
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
        """Update API crawler configuration"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning("Cannot update configuration while crawler is running")
                return False
            
            if not self.validate_config(config):
                return False
            
            self.config.update(config)
            self.base_url = config.get('base_url', self.base_url)
            self.api_key = config.get('api_key', self.api_key)
            self.endpoints = config.get('endpoints', self.endpoints)
            self.rate_limit = config.get('rate_limit', self.rate_limit)
            
            logger.info(f"Updated configuration for API crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to update configuration: {str(e)}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate API crawler configuration"""
        try:
            base_url = config.get('base_url', self.base_url)
            if not base_url:
                self._set_error("base_url is required")
                return False
            
            if not base_url.startswith(('http://', 'https://')):
                self._set_error("base_url must be a valid HTTP/HTTPS URL")
                return False
            
            endpoints = config.get('endpoints', self.endpoints)
            if not isinstance(endpoints, list):
                self._set_error("endpoints must be a list")
                return False
            
            rate_limit = config.get('rate_limit', self.rate_limit)
            if not isinstance(rate_limit, (int, float)) or rate_limit < 0:
                self._set_error("rate_limit must be a non-negative number")
                return False
            
            return True
            
        except Exception as e:
            self._set_error(f"Configuration validation failed: {str(e)}")
            return False
    
    def _crawl_endpoints(self):
        """Internal method to crawl all configured endpoints"""
        try:
            for endpoint in self.endpoints:
                if not self._running or self.status == CrawlerStatus.PAUSED:
                    break
                
                self._fetch_endpoint(endpoint)
                
                # Respect rate limit
                if self.rate_limit > 0:
                    asyncio.sleep(self.rate_limit)
            
            if self._running:
                self.status = CrawlerStatus.COMPLETED
                self._finalize_stats()
                
        except Exception as e:
            self._set_error(f"Crawling failed: {str(e)}")
            self.status = CrawlerStatus.ERROR
    
    def _fetch_endpoint(self, endpoint: str):
        """Fetch data from a single endpoint"""
        try:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            
            with self.session.get(url) as response:
                if response.status == 200:
                    data = response.json()
                    self.stats.items_scraped += len(data) if isinstance(data, list) else 1
                    self.stats.pages_visited += 1
                    
                    # Process the data (implement your logic here)
                    self._process_data(endpoint, data)
                    
                    logger.debug(f"Successfully fetched {endpoint}")
                else:
                    logger.warning(f"HTTP {response.status} for {endpoint}")
                    self.stats.errors_count += 1
                    
        except Exception as e:
            logger.error(f"Failed to fetch {endpoint}: {str(e)}")
            self.stats.errors_count += 1
    
    def _process_data(self, endpoint: str, data: Any):
        """Process fetched data - override this method for custom processing"""
        # This is where you would implement your data processing logic
        # For example: save to database, transform data, etc.
        logger.info(f"Processing data from {endpoint}: {len(data) if isinstance(data, list) else 1} items")
    
    def _finalize_stats(self):
        """Finalize crawler statistics"""
        self.stats.end_time = datetime.now()
        if self.stats.start_time:
            self.stats.duration = (self.stats.end_time - self.stats.start_time).total_seconds()


# Configuration example for API crawler
API_CONFIG_EXAMPLE = {
    'base_url': 'https://api.example.com',
    'api_key': 'your-api-key-here',
    'endpoints': [
        'users',
        'posts',
        'comments'
    ],
    'rate_limit': 1.0,  # 1 second between requests
    'timeout': 30
}


def create_api_crawler(name: str, base_url: str, **kwargs) -> 'CustomAPICrawler':
    """Convenience function to create an API crawler"""
    config = API_CONFIG_EXAMPLE.copy()
    config['base_url'] = base_url
    config.update(kwargs)
    return CustomAPICrawler(name, config)


# Example of how to register this custom crawler type
def register_api_crawler():
    """Register the API crawler with the factory"""
    from src.crawlers.impl import CrawlerFactory
    CrawlerFactory.register_crawler_type('api', CustomAPICrawler)
    logger.info("Registered API crawler type")


# Example usage
def example_api_crawler_usage():
    """Example of how to use the custom API crawler"""
    
    # Register the custom crawler type
    register_api_crawler()
    
    # Create an API crawler using the factory
    from src.crawlers.impl import CrawlerFactory
    
    api_crawler = CrawlerFactory.create_crawler(
        'api',
        'my_api_crawler',
        {
            'base_url': 'https://jsonplaceholder.typicode.com',
            'endpoints': ['posts', 'users', 'comments'],
            'rate_limit': 0.5
        }
    )
    
    # Start the crawler
    api_crawler.start()
    
    # Wait a bit for it to work
    asyncio.sleep(5)
    
    # Check status
    status = api_crawler.get_status()
    print(f"Crawler status: {status}")
    
    # Stop the crawler
    api_crawler.stop()


# if __name__ == "__main__":
#     asyncio.run(example_api_crawler_usage())