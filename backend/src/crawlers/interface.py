import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Type

logger = logging.getLogger(__name__)


class CrawlerStatus(Enum):
    """Enumeration of possible crawler states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    ERROR = "error"
    COMPLETED = "completed"


@dataclass
class CrawlerStats:
    """Data class to hold crawler statistics"""
    items_scraped: int = 0
    pages_visited: int = 0
    errors_count: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration: Optional[float] = None


class CrawlerInterface(ABC):
    """Abstract base class defining the crawler interface"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.status = CrawlerStatus.IDLE
        self.stats = CrawlerStats()
        self._error_message: Optional[str] = None
    
    @abstractmethod
    def start(self, **kwargs) -> bool:
        """
        Start the crawler
        
        Args:
            **kwargs: Additional parameters for starting the crawler
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def stop(self) -> bool:
        """
        Stop the crawler
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def pause(self) -> bool:
        """
        Pause the crawler
        
        Returns:
            bool: True if paused successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def resume(self) -> bool:
        """
        Resume the crawler from paused state
        
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status and statistics of the crawler
        
        Returns:
            Dict containing status, stats, and other relevant information
        """
        pass
    
    # @abstractmethod
    # def configure(self, config: Dict[str, Any]) -> bool:
    #     """
    #     Update crawler configuration
        
    #     Args:
    #         config: New configuration parameters
            
    #     Returns:
    #         bool: True if configuration updated successfully
    #     """
    #     pass
    
    # @abstractmethod
    # def validate_config(self, config: Dict[str, Any]) -> bool:
    #     """
    #     Validate crawler configuration
        
    #     Args:
    #         config: Configuration to validate
            
    #     Returns:
    #         bool: True if configuration is valid
    #     """
    #     pass
    
    def get_error_message(self) -> Optional[str]:
        """Get the last error message if any"""
        return self._error_message
    
    def _set_error(self, message: str):
        """Set error status and message"""
        self.status = CrawlerStatus.ERROR
        self._error_message = message
        logger.error(f"Crawler {self.name} error: {message}")
    
    def _clear_error(self):
        """Clear error status and message"""
        self._error_message = None
    
    def _update_stats(self, **kwargs):
        """Update crawler statistics"""
        for key, value in kwargs.items():
            if hasattr(self.stats, key):
                setattr(self.stats, key, value)
    
    def is_running(self) -> bool:
        """Check if crawler is currently running"""
        return self.status == CrawlerStatus.RUNNING
    
    def is_idle(self) -> bool:
        """Check if crawler is idle"""
        return self.status == CrawlerStatus.IDLE
    
    def has_error(self) -> bool:
        """Check if crawler has an error"""
        return self.status == CrawlerStatus.ERROR


class CrawlerManager:
    """Manager class to handle multiple crawlers"""
    
    def __init__(self):
        self.crawlers: Dict[str, CrawlerInterface] = {}
    
    def add_crawler(self, crawler: CrawlerInterface):
        """Add a crawler to the manager"""
        self.crawlers[crawler.name] = crawler
        logger.info(f"Added crawler to manager: {crawler.name}")
    
    def get_crawler(self, name: str) -> Optional[CrawlerInterface]:
        """Get a crawler by name"""
        return self.crawlers.get(name)
    
    def remove_crawler(self, name: str) -> bool:
        """Remove a crawler from the manager"""
        if name in self.crawlers:
            del self.crawlers[name]
            logger.info(f"Removed crawler from manager: {name}")
            return True
        return False
    
    def list_crawlers(self) -> list:
        """Get list of all crawler names"""
        return list(self.crawlers.keys())
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all crawlers"""
        return {name: crawler.get_status() for name, crawler in self.crawlers.items()}
    
    def get_running_crawlers(self) -> Dict[str, CrawlerInterface]:
        """Get all currently running crawlers"""
        return {
            name: crawler 
            for name, crawler in self.crawlers.items() 
            if crawler.is_running()
        }
    
    def stop_all(self):
        """Stop all running crawlers"""
        for crawler in self.crawlers.values():
            if crawler.is_running():
                crawler.stop()
        logger.info("Stopped all running crawlers")
    
    def pause_all(self):
        """Pause all running crawlers"""
        for crawler in self.crawlers.values():
            if crawler.is_running():
                crawler.pause()
        logger.info("Paused all running crawlers")
