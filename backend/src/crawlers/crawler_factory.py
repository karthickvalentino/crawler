"""
Crawler Factory Module

This module provides a unified interface for creating and managing different types of crawlers.
Currently supports Scrapy spiders and Selenium crawlers with extensibility for other crawler types.
"""

from .interface import (
    CrawlerInterface,
    CrawlerStatus,
    CrawlerStats,
    CrawlerManager
)

from .impl import (
    CrawlerFactory,
    create_and_configure_scrapy_crawler,
    create_and_configure_selenium_crawler,
    test_crawler_creation
)

from src.crawlers.implementations import (
    ScrapyCrawler,
    SeleniumCrawler,
    SCRAPY_CONFIG_EXAMPLE,
    SELENIUM_CONFIG_EXAMPLE,
    create_scrapy_crawler,
    create_selenium_crawler
)

import logging
from typing import Dict, Any, Optional, List
# import asyncio

logger = logging.getLogger(__name__)

# Global crawler manager instance
crawler_manager = CrawlerManager()


def get_crawler_manager() -> CrawlerManager:
    """Get the global crawler manager instance"""
    return crawler_manager


def create_and_register_crawler(
    crawler_type: str, 
    name: str, 
    config: Dict[str, Any],
    auto_register: bool = True
) -> CrawlerInterface:
    """
    Create a crawler and optionally register it with the global manager
    
    Args:
        crawler_type: Type of crawler ('scrapy', 'selenium', etc.)
        name: Unique name for the crawler
        config: Configuration dictionary
        auto_register: Whether to automatically register with global manager
        
    Returns:
        CrawlerInterface: Created crawler instance
    """
    crawler = CrawlerFactory.create_crawler(crawler_type, name, config)
    
    if auto_register:
        crawler_manager.add_crawler(crawler)
    
    return crawler


def get_supported_crawler_types() -> List[str]:
    """Get list of all supported crawler types"""
    return CrawlerFactory.get_supported_types()


def register_custom_crawler_type(crawler_type: str, crawler_class):
    """
    Register a custom crawler type
    
    Args:
        crawler_type: String identifier for the crawler type
        crawler_class: Class implementing CrawlerInterface
    """
    CrawlerFactory.register_crawler_type(crawler_type, crawler_class)


def get_crawler_type_info(crawler_type: str) -> Dict[str, Any]:
    """
    Get information about a specific crawler type
    
    Args:
        crawler_type: Type of crawler
        
    Returns:
        Dict containing crawler information
    """
    return CrawlerFactory.get_crawler_info(crawler_type)


def list_all_crawler_types_info() -> Dict[str, Dict[str, Any]]:
    """Get detailed information about all registered crawler types"""
    return CrawlerFactory.list_all_crawler_info()


# Convenience functions for creating specific crawler types
def create_scrapy_crawler_with_settings(
    name: str,
    spider_name: str,
    custom_settings: Dict[str, Any] = None,
    auto_register: bool = True,
    **kwargs
) -> ScrapyCrawler:
    """
    Create a Scrapy crawler with custom settings and optionally register it
    
    Args:
        name: Crawler name
        spider_name: Name of the Scrapy spider
        custom_settings: Custom Scrapy settings to override defaults
        auto_register: Whether to register with global manager
        **kwargs: Additional configuration options
        
    Returns:
        ScrapyCrawler: Configured Scrapy crawler instance
    """
    crawler = create_and_configure_scrapy_crawler(
        name=name,
        spider_name=spider_name,
        settings=custom_settings,
        **kwargs
    )
    
    if auto_register:
        crawler_manager.add_crawler(crawler)
    
    return crawler


def create_selenium_crawler_with_options(
    name: str,
    driver_type: str = 'chrome',
    headless: bool = True,
    custom_options: Dict[str, Any] = None,
    auto_register: bool = True,
    **kwargs
) -> SeleniumCrawler:
    """
    Create a Selenium crawler with custom options and optionally register it
    
    Args:
        name: Crawler name
        driver_type: Type of WebDriver ('chrome', 'firefox', etc.)
        headless: Whether to run in headless mode
        custom_options: Custom driver options
        auto_register: Whether to register with global manager
        **kwargs: Additional configuration options
        
    Returns:
        SeleniumCrawler: Configured Selenium crawler instance
    """
    crawler = create_and_configure_selenium_crawler(
        name=name,
        driver_type=driver_type,
        headless=headless,
        custom_options=custom_options,
        **kwargs
    )
    
    if auto_register:
        crawler_manager.add_crawler(crawler)
    
    return crawler


# Manager utility functions
def start_crawler_by_name(name: str, _crawler=None, **kwargs) -> bool:
    """
    Start a crawler by name from the global manager
    
    Args:
        name: Name of the crawler to start
        **kwargs: Additional parameters for starting
        
    Returns:
        bool: True if started successfully
    """
    crawler = crawler_manager.get_crawler(name)
    if crawler:
        return crawler.start(**kwargs)
    
    if  _crawler:
        return _crawler.start(**kwargs)
    
    logger.error(f"Crawler not found: {name}")
    return False


def stop_crawler_by_name(name: str) -> bool:
    """
    Stop a crawler by name from the global manager
    
    Args:
        name: Name of the crawler to stop
        
    Returns:
        bool: True if stopped successfully
    """
    crawler = crawler_manager.get_crawler(name)
    if crawler:
        return crawler.stop()
    
    logger.error(f"Crawler not found: {name}")
    return False


def pause_crawler_by_name(name: str) -> bool:
    """
    Pause a crawler by name from the global manager
    
    Args:
        name: Name of the crawler to pause
        
    Returns:
        bool: True if paused successfully
    """
    crawler = crawler_manager.get_crawler(name)
    if crawler:
        return crawler.pause()
    
    logger.error(f"Crawler not found: {name}")
    return False


def resume_crawler_by_name(name: str) -> bool:
    """
    Resume a crawler by name from the global manager
    
    Args:
        name: Name of the crawler to resume
        
    Returns:
        bool: True if resumed successfully
    """
    crawler = crawler_manager.get_crawler(name)
    if crawler:
        return crawler.resume()
    
    logger.error(f"Crawler not found: {name}")
    return False


def get_crawler_status_by_name(name: str) -> Optional[Dict[str, Any]]:
    """
    Get status of a crawler by name
    
    Args:
        name: Name of the crawler
        
    Returns:
        Dict containing status information or None if not found
    """
    crawler = crawler_manager.get_crawler(name)
    if crawler:
        return crawler.get_status()
    
    logger.error(f"Crawler not found: {name}")
    return None


# Batch operations
def start_all_crawlers(**kwargs) -> Dict[str, bool]:
    """
    Start all registered crawlers
    
    Args:
        **kwargs: Additional parameters for starting crawlers
        
    Returns:
        Dict mapping crawler names to start success status
    """
    results = {}
    for name, crawler in crawler_manager.crawlers.items():
        if not crawler.is_running():
            results[name] = crawler.start(**kwargs)
        else:
            results[name] = True  # Already running
            
    return results


def stop_all_crawlers() -> Dict[str, bool]:
    """
    Stop all registered crawlers
    
    Returns:
        Dict mapping crawler names to stop success status
    """
    results = {}
    for name, crawler in crawler_manager.crawlers.items():
        if crawler.is_running():
            results[name] = crawler.stop()
        else:
            results[name] = True  # Already stopped
            
    return results


def get_all_crawler_statuses() -> Dict[str, Dict[str, Any]]:
    """Get status of all registered crawlers"""
    return crawler_manager.get_all_status()


def get_running_crawler_names() -> List[str]:
    """Get names of all currently running crawlers"""
    return list(crawler_manager.get_running_crawlers().keys())


# Example usage and demo functions
def demo_crawler_usage():
    """Demonstrate crawler usage with examples"""
    print("=== Crawler Factory Demo ===")
    
    try:
        # Create Scrapy crawler
        scrapy_crawler = create_scrapy_crawler_with_settings(
            name="demo_scrapy",
            spider_name="quotes_spider",
            custom_settings={
                'DOWNLOAD_DELAY': 2,
                'CONCURRENT_REQUESTS': 8
            }
        )
        print(f"Created Scrapy crawler: {scrapy_crawler.name}")
        
        # Create Selenium crawler
        selenium_crawler = create_selenium_crawler_with_options(
            name="demo_selenium",
            driver_type="chrome",
            headless=True,
            custom_options={
                'disable_images': True
            }
        )
        print(f"Created Selenium crawler: {selenium_crawler.name}")
        
        # Show all registered crawlers
        print(f"Registered crawlers: {crawler_manager.list_crawlers()}")
        
        # Show supported types
        print(f"Supported crawler types: {get_supported_crawler_types()}")
        
        # Show detailed type information
        print("Crawler type information:")
        for crawler_type, info in list_all_crawler_types_info().items():
            print(f"  {crawler_type}: {info['class_name']}")
        
        # Test starting and stopping
        print("\n=== Testing Crawler Operations ===")
        
        # Start Selenium crawler (Scrapy requires actual spider setup)
        if start_crawler_by_name("demo_selenium"):
            print("Started demo_selenium crawler")
            
            # Get status
            status = get_crawler_status_by_name("demo_selenium")
            if status:
                print(f"Selenium crawler status: {status['status']}")
            
            # Stop crawler
            if stop_crawler_by_name("demo_selenium"):
                print("Stopped demo_selenium crawler")
        
        print("Demo completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        return False


# Export main components
__all__ = [
    # Interfaces and enums
    'CrawlerInterface',
    'CrawlerStatus', 
    'CrawlerStats',
    'CrawlerManager',
    
    # Factory and implementations
    'CrawlerFactory',
    'ScrapyCrawler',
    'SeleniumCrawler',
    
    # Utility functions
    'create_scrapy_crawler',
    'create_selenium_crawler',
    'create_and_register_crawler',
    'create_scrapy_crawler_with_settings',
    'create_selenium_crawler_with_options',
    
    # Manager functions
    'get_crawler_manager',
    'start_crawler_by_name',
    'stop_crawler_by_name',
    'pause_crawler_by_name',
    'resume_crawler_by_name',
    'get_crawler_status_by_name',
    
    # Batch operations
    'start_all_crawlers',
    'stop_all_crawlers',
    'get_all_crawler_statuses',
    'get_running_crawler_names',
    
    # Information functions
    'get_supported_crawler_types',
    'get_crawler_type_info',
    'list_all_crawler_types_info',
    'register_custom_crawler_type',
    
    # Configuration examples
    'SCRAPY_CONFIG_EXAMPLE',
    'SELENIUM_CONFIG_EXAMPLE',
    
    # Global manager
    'crawler_manager',
    
    # Demo and testing
    'demo_crawler_usage',
    'test_crawler_creation'
]


# if __name__ == "__main__":
    # Run demo
    # asyncio.run(demo_crawler_usage())