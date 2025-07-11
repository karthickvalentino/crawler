from typing import Dict, Any, Optional
import logging
from datetime import datetime
from src.crawlers.interface import CrawlerInterface, CrawlerStatus

logger = logging.getLogger(__name__)


class SeleniumCrawler(CrawlerInterface):
    """Selenium-based crawler implementation"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.driver = None
        self.driver_type = config.get('driver_type', 'chrome')
        self.headless = config.get('headless', True)
        self.timeout = config.get('timeout', 30)
        self.window_size = config.get('window_size', (1920, 1080))
        self.user_agent = config.get('user_agent')
        self.driver_options = config.get('options', {})
    
    def start(self, **kwargs) -> bool:
        """Start the Selenium crawler"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning(f"Crawler {self.name} is already running")
                return False
            
            self._clear_error()
            
            # Initialize WebDriver
            self.driver = self._create_driver()
            
            if not self.driver:
                self._set_error("Failed to create WebDriver")
                return False
            
            # Set window size
            self.driver.set_window_size(*self.window_size)
            
            # Set implicit wait timeout
            self.driver.implicitly_wait(self.timeout)
            
            self.status = CrawlerStatus.RUNNING
            self.stats.start_time = datetime.now()
            
            logger.info(f"Started Selenium crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to start Selenium crawler: {str(e)}")
            return False
    
    def stop(self) -> bool:
        """Stop the Selenium crawler"""
        try:
            if self.driver:
                self.driver.quit()
                self.driver = None
            
            self._finalize_stats()
            self.status = CrawlerStatus.STOPPED
            
            logger.info(f"Stopped Selenium crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to stop Selenium crawler: {str(e)}")
            return False
    
    def pause(self) -> bool:
        """Pause the Selenium crawler"""
        if self.status != CrawlerStatus.RUNNING:
            logger.warning(f"Cannot pause crawler {self.name} - not running")
            return False
        
        self.status = CrawlerStatus.PAUSED
        logger.info(f"Paused Selenium crawler: {self.name}")
        return True
    
    def resume(self) -> bool:
        """Resume the Selenium crawler"""
        if self.status != CrawlerStatus.PAUSED:
            logger.warning(f"Cannot resume crawler {self.name} - not paused")
            return False
        
        self.status = CrawlerStatus.RUNNING
        logger.info(f"Resumed Selenium crawler: {self.name}")
        return True
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the Selenium crawler"""
        return {
            'name': self.name,
            'type': 'selenium',
            'status': self.status.value,
            'driver_type': self.driver_type,
            'headless': self.headless,
            'timeout': self.timeout,
            'window_size': self.window_size,
            'current_url': self.driver.current_url if self.driver else None,
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
        """Update Selenium crawler configuration"""
        try:
            if self.status == CrawlerStatus.RUNNING:
                logger.warning("Cannot update configuration while crawler is running")
                return False
            
            if not self.validate_config(config):
                return False
            
            self.config.update(config)
            self.driver_type = config.get('driver_type', self.driver_type)
            self.headless = config.get('headless', self.headless)
            self.timeout = config.get('timeout', self.timeout)
            self.window_size = config.get('window_size', self.window_size)
            self.user_agent = config.get('user_agent', self.user_agent)
            self.driver_options = config.get('options', self.driver_options)
            
            logger.info(f"Updated configuration for Selenium crawler: {self.name}")
            return True
            
        except Exception as e:
            self._set_error(f"Failed to update configuration: {str(e)}")
            return False
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate Selenium crawler configuration"""
        try:
            driver_type = config.get('driver_type', self.driver_type)
            if driver_type not in ['chrome', 'firefox', 'edge', 'safari']:
                self._set_error(f"Unsupported driver type: {driver_type}")
                return False
            
            timeout = config.get('timeout', self.timeout)
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                self._set_error("Timeout must be a positive number")
                return False
            
            window_size = config.get('window_size', self.window_size)
            if not isinstance(window_size, (list, tuple)) or len(window_size) != 2:
                self._set_error("Window size must be a tuple/list of (width, height)")
                return False
            
            return True
            
        except Exception as e:
            self._set_error(f"Configuration validation failed: {str(e)}")
            return False
    
    def _create_driver(self):
        """Create WebDriver instance based on configuration"""
        try:
            from selenium import webdriver
            from selenium.webdriver.chrome.options import Options as ChromeOptions
            from selenium.webdriver.firefox.options import Options as FirefoxOptions
            from selenium.webdriver.edge.options import Options as EdgeOptions
            
            if self.driver_type.lower() == 'chrome':
                options = ChromeOptions()
                if self.headless:
                    options.add_argument('--headless')
                if self.user_agent:
                    options.add_argument(f'--user-agent={self.user_agent}')
                
                # Add custom options
                if self.driver_options.get('disable_images'):
                    options.add_argument('--blink-settings=imagesEnabled=false')
                if self.driver_options.get('disable_javascript'):
                    options.add_argument('--disable-javascript')
                
                return webdriver.Chrome(options=options)
                
            elif self.driver_type.lower() == 'firefox':
                options = FirefoxOptions()
                if self.headless:
                    options.add_argument('--headless')
                if self.user_agent:
                    options.set_preference("general.useragent.override", self.user_agent)
                
                return webdriver.Firefox(options=options)
                
            elif self.driver_type.lower() == 'edge':
                options = EdgeOptions()
                if self.headless:
                    options.add_argument('--headless')
                if self.user_agent:
                    options.add_argument(f'--user-agent={self.user_agent}')
                
                return webdriver.Edge(options=options)
                
            else:
                raise ValueError(f"Unsupported driver type: {self.driver_type}")
                
        except Exception as e:
            logger.error(f"Failed to create {self.driver_type} driver: {str(e)}")
            return None
    
    def _finalize_stats(self):
        """Finalize crawler statistics"""
        self.stats.end_time = datetime.now()
        if self.stats.start_time:
            self.stats.duration = (self.stats.end_time - self.stats.start_time).total_seconds()
    
    # Selenium-specific utility methods
    def navigate_to(self, url: str) -> bool:
        """Navigate to a URL"""
        try:
            if not self.driver:
                logger.error("Driver not initialized")
                return False
            
            self.driver.get(url)
            self.stats.pages_visited += 1
            return True
            
        except Exception as e:
            self.stats.errors_count += 1
            logger.error(f"Failed to navigate to {url}: {str(e)}")
            return False
    
    def find_element(self, by, value):
        """Find element using Selenium locators"""
        try:
            if not self.driver:
                return None
            return self.driver.find_element(by, value)
        except Exception as e:
            logger.error(f"Failed to find element {by}={value}: {str(e)}")
            return None
    
    def find_elements(self, by, value):
        """Find elements using Selenium locators"""
        try:
            if not self.driver:
                return []
            return self.driver.find_elements(by, value)
        except Exception as e:
            logger.error(f"Failed to find elements {by}={value}: {str(e)}")
            return []
    
    def execute_script(self, script: str, *args):
        """Execute JavaScript in the browser"""
        try:
            if not self.driver:
                return None
            return self.driver.execute_script(script, *args)
        except Exception as e:
            logger.error(f"Failed to execute script: {str(e)}")
            return None
    
    def take_screenshot(self, filename: str = None) -> bool:
        """Take a screenshot"""
        try:
            if not self.driver:
                return False
            
            if filename:
                return self.driver.save_screenshot(filename)
            else:
                return self.driver.get_screenshot_as_png()
                
        except Exception as e:
            logger.error(f"Failed to take screenshot: {str(e)}")
            return False


# Configuration example for Selenium crawler
SELENIUM_CONFIG_EXAMPLE = {
    'driver_type': 'chrome',
    'headless': True,
    'timeout': 30,
    'window_size': (1920, 1080),
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'options': {
        'disable_images': True,
        'disable_javascript': False,
        'page_load_strategy': 'normal'
    }
}


def create_selenium_crawler(name: str, driver_type: str = 'chrome', **kwargs) -> 'SeleniumCrawler':
    """Convenience function to create a Selenium crawler"""
    config = SELENIUM_CONFIG_EXAMPLE.copy()
    config['driver_type'] = driver_type
    config.update(kwargs)
    return SeleniumCrawler(name, config)