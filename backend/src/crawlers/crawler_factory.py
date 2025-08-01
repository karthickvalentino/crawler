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

from .scrapy_crawler import ScrapyCrawler, create_scrapy_crawler

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
    name: str, 
    config: Dict[str, Any],
    auto_register: bool = True
) -> CrawlerInterface:
    """
    Create a crawler and optionally register it with the global manager
    
    Args:
        name: Unique name for the crawler
        config: Configuration dictionary
        auto_register: Whether to automatically register with global manager
        
    Returns:
        CrawlerInterface: Created crawler instance
    """
    crawler = create_scrapy_crawler(name, **config)
    
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


# Export main components
__all__ = [
    # Interfaces and enums
    'CrawlerInterface',
    'CrawlerStatus', 
    'CrawlerStats',
    'CrawlerManager',
    
    # Factory and implementations
    'ScrapyCrawler',
    
    # Utility functions
    'create_scrapy_crawler',
    'create_and_register_crawler',
    
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
    
    # Global manager
    'crawler_manager',
]