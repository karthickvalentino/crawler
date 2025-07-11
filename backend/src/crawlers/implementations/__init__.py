"""
Crawler Implementations Package

This package contains specific implementations of the CrawlerInterface
for different crawler types (Scrapy, Selenium, API, etc.)
"""

from .scrapy_crawler import (
    ScrapyCrawler,
    SCRAPY_CONFIG_EXAMPLE,
    create_scrapy_crawler
)

from .selenium_crawler import (
    SeleniumCrawler,
    SELENIUM_CONFIG_EXAMPLE,
    create_selenium_crawler
)

from .custom_example import (
    CustomAPICrawler,
    API_CONFIG_EXAMPLE,
    create_api_crawler,
    register_api_crawler
)

__all__ = [
    # Scrapy implementation
    'ScrapyCrawler',
    'SCRAPY_CONFIG_EXAMPLE',
    'create_scrapy_crawler',
    
    # Selenium implementation
    'SeleniumCrawler',
    'SELENIUM_CONFIG_EXAMPLE',
    'create_selenium_crawler',
    
    # Custom API implementation (example)
    'CustomAPICrawler',
    'API_CONFIG_EXAMPLE',
    'create_api_crawler',
    'register_api_crawler'
]