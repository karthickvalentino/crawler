from typing import Dict, Any, Type, List
import logging
from .interface import CrawlerInterface
from .implementations import (
    ScrapyCrawler,
    SeleniumCrawler,
    SCRAPY_CONFIG_EXAMPLE,
    SELENIUM_CONFIG_EXAMPLE,
    create_scrapy_crawler,
    create_selenium_crawler
)

logger = logging.getLogger(__name__)


class CrawlerFactory:
    """Factory class for creating crawler instances"""
    
    _crawler_types: Dict[str, Type[CrawlerInterface]] = {
        'scrapy': ScrapyCrawler,
        'selenium': SeleniumCrawler,
    }
    
    @classmethod
    def register_crawler_type(cls, crawler_type: str, crawler_class: Type[CrawlerInterface]):
        """
        Register a new crawler type
        
        Args:
            crawler_type: String identifier for the crawler type
            crawler_class: Class that implements CrawlerInterface
        """
        if not issubclass(crawler_class, CrawlerInterface):
            raise ValueError(f"Crawler class must implement CrawlerInterface")
        
        cls._crawler_types[crawler_type] = crawler_class
        logger.info(f"Registered crawler type: {crawler_type}")
    
    @classmethod
    def create_crawler(cls, crawler_type: str, name: str, config: Dict[str, Any]) -> CrawlerInterface:
        """
        Create a crawler instance
        
        Args:
            crawler_type: Type of crawler to create ('scrapy', 'selenium', etc.)
            name: Name for the crawler instance
            config: Configuration dictionary
            
        Returns:
            CrawlerInterface: Crawler instance
            
        Raises:
            ValueError: If crawler_type is not supported
        """
        if crawler_type not in cls._crawler_types:
            raise ValueError(f"Unsupported crawler type: {crawler_type}. "
                           f"Available types: {list(cls._crawler_types.keys())}")
        
        crawler_class = cls._crawler_types[crawler_type]
        
        try:
            crawler_instance = crawler_class(name, config)
            logger.info(f"Created {crawler_type} crawler: {name}")
            return crawler_instance
        except Exception as e:
            logger.error(f"Failed to create {crawler_type} crawler {name}: {str(e)}")
            raise
    
    @classmethod
    def get_supported_types(cls) -> List[str]:
        """Get list of supported crawler types"""
        return list(cls._crawler_types.keys())
    
    @classmethod
    def unregister_crawler_type(cls, crawler_type: str) -> bool:
        """
        Unregister a crawler type
        
        Args:
            crawler_type: Type to unregister
            
        Returns:
            bool: True if unregistered successfully
        """
        if crawler_type in cls._crawler_types:
            del cls._crawler_types[crawler_type]
            logger.info(f"Unregistered crawler type: {crawler_type}")
            return True
        return False
    
    @classmethod
    def get_crawler_info(cls, crawler_type: str) -> Dict[str, Any]:
        """
        Get information about a specific crawler type
        
        Args:
            crawler_type: Type of crawler
            
        Returns:
            Dict containing crawler information
        """
        if crawler_type not in cls._crawler_types:
            return {}
        
        crawler_class = cls._crawler_types[crawler_type]
        return {
            'type': crawler_type,
            'class_name': crawler_class.__name__,
            'module': crawler_class.__module__,
            'doc': crawler_class.__doc__
        }
    
    @classmethod
    def list_all_crawler_info(cls) -> Dict[str, Dict[str, Any]]:
        """Get information about all registered crawler types"""
        return {
            crawler_type: cls.get_crawler_info(crawler_type)
            for crawler_type in cls._crawler_types.keys()
        }


# Utility functions for creating specific crawler types
def create_and_configure_scrapy_crawler(
    name: str,
    spider_name: str,
    settings: Dict[str, Any] = None,
    **kwargs
) -> ScrapyCrawler:
    """
    Create and configure a Scrapy crawler with custom settings
    
    Args:
        name: Crawler name
        spider_name: Name of the Scrapy spider
        settings: Custom Scrapy settings
        **kwargs: Additional configuration options
        
    Returns:
        ScrapyCrawler: Configured Scrapy crawler instance
    """
    config = SCRAPY_CONFIG_EXAMPLE.copy()
    config['spider_name'] = spider_name
    
    if settings:
        config['settings'].update(settings)
    
    config.update(kwargs)
    
    return CrawlerFactory.create_crawler('scrapy', name, config)


def create_and_configure_selenium_crawler(
    name: str,
    driver_type: str = 'chrome',
    headless: bool = True,
    custom_options: Dict[str, Any] = None,
    **kwargs
) -> SeleniumCrawler:
    """
    Create and configure a Selenium crawler with custom options
    
    Args:
        name: Crawler name
        driver_type: Type of WebDriver ('chrome', 'firefox', etc.)
        headless: Whether to run in headless mode
        custom_options: Custom driver options
        **kwargs: Additional configuration options
        
    Returns:
        SeleniumCrawler: Configured Selenium crawler instance
    """
    config = SELENIUM_CONFIG_EXAMPLE.copy()
    config['driver_type'] = driver_type
    config['headless'] = headless
    
    if custom_options:
        config['options'].update(custom_options)
    
    config.update(kwargs)
    
    return CrawlerFactory.create_crawler('selenium', name, config)


# Example usage and testing functions
def test_crawler_creation():
    """Test function to demonstrate crawler creation"""
    try:
        # Test Scrapy crawler creation
        scrapy_crawler = CrawlerFactory.create_crawler(
            'scrapy',
            'test_scrapy',
            SCRAPY_CONFIG_EXAMPLE
        )
        print(f"Created Scrapy crawler: {scrapy_crawler.name}")
        
        # Test Selenium crawler creation
        selenium_crawler = CrawlerFactory.create_crawler(
            'selenium',
            'test_selenium',
            SELENIUM_CONFIG_EXAMPLE
        )
        print(f"Created Selenium crawler: {selenium_crawler.name}")
        
        # Test factory info methods
        print(f"Supported types: {CrawlerFactory.get_supported_types()}")
        print(f"All crawler info: {CrawlerFactory.list_all_crawler_info()}")
        
        return True
        
    except Exception as e:
        logger.error(f"Test failed: {str(e)}")
        return False


# Export main components
__all__ = [
    # Factory
    'CrawlerFactory',
    
    # Implementations
    'ScrapyCrawler',
    'SeleniumCrawler',
    
    # Utility functions
    'create_scrapy_crawler',
    'create_selenium_crawler',
    'create_and_configure_scrapy_crawler',
    'create_and_configure_selenium_crawler',
    
    # Configuration examples
    'SCRAPY_CONFIG_EXAMPLE',
    'SELENIUM_CONFIG_EXAMPLE',
    
    # Test function
    'test_crawler_creation'
]


# if __name__ == "__main__":
    # import asyncio
    # asyncio.run(test_crawler_creation())