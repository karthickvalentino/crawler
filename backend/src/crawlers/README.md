# Crawler System Documentation

This document describes the reorganized crawler system with modular implementations.

## Structure

```
backend/src/crawlers/
├── __init__.py                     # Package initialization
├── interface.py                    # Base interfaces and enums
├── impl.py                        # Main implementation with factory
├── crawler_factory.py             # Main entry point and utilities
├── implementations/                # Specific crawler implementations
│   ├── __init__.py
│   ├── scrapy_crawler.py          # Scrapy-based crawler
│   ├── selenium_crawler.py        # Selenium-based crawler
│   └── custom_example.py          # Example custom crawler
└── examples/
    └── usage_example.py           # Comprehensive usage examples
```

## Quick Start

### Basic Usage

```python
from backend.src.crawlers.crawler_factory import (
    create_scrapy_crawler_with_settings,
    create_selenium_crawler_with_options,
    start_crawler_by_name,
    stop_crawler_by_name
)

# Create a Scrapy crawler
scrapy_crawler = create_scrapy_crawler_with_settings(
    name="my_scraper",
    spider_name="quotes_spider",
    custom_settings={
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 8
    }
)

# Create a Selenium crawler
selenium_crawler = create_selenium_crawler_with_options(
    name="dynamic_scraper",
    driver_type="chrome",
    headless=True,
    custom_options={'disable_images': True}
)

# Start crawlers
await start_crawler_by_name("my_scraper")
await start_crawler_by_name("dynamic_scraper")

# Stop crawlers
await stop_crawler_by_name("my_scraper")
await stop_crawler_by_name("dynamic_scraper")
```

### Creating Custom Crawlers

```python
from backend.src.crawlers.interface import CrawlerInterface, CrawlerStatus
from backend.src.crawlers.impl import CrawlerFactory

class MyCrawler(CrawlerInterface):
    async def start(self, **kwargs) -> bool:
        # Implementation here
        pass
    
    async def stop(self) -> bool:
        # Implementation here
        pass
    
    # ... other required methods

# Register your custom crawler
CrawlerFactory.register_crawler_type('mycrawler', MyCrawler)

# Create instance
crawler = CrawlerFactory.create_crawler('mycrawler', 'my_instance', config)
```

## Available Crawler Types

### 1. Scrapy Crawler (`scrapy`)

For web scraping using the Scrapy framework.

**Configuration:**
```python
{
    'spider_name': 'my_spider',
    'spider_class': MySpiderClass,  # Optional
    'spider_module': 'myproject.spiders.my_spider',
    'settings': {
        'DOWNLOAD_DELAY': 1,
        'CONCURRENT_REQUESTS': 16,
        'ROBOTSTXT_OBEY': True
    }
}
```

### 2. Selenium Crawler (`selenium`)

For browser automation and dynamic content scraping.

**Configuration:**
```python
{
    'driver_type': 'chrome',  # chrome, firefox, edge, safari
    'headless': True,
    'timeout': 30,
    'window_size': (1920, 1080),
    'user_agent': 'Custom User Agent',
    'options': {
        'disable_images': True,
        'disable_javascript': False
    }
}
```

### 3. Custom API Crawler (`api`)

Example implementation for REST API crawling.

**Configuration:**
```python
{
    'base_url': 'https://api.example.com',
    'api_key': 'your-api-key',
    'endpoints': ['users', 'posts', 'comments'],
    'rate_limit': 1.0,
    'timeout': 30
}
```

## Key Features

### 1. Factory Pattern
- Centralized crawler creation
- Type registration system
- Easy extensibility

### 2. Unified Interface
- Consistent API across all crawler types
- Standard lifecycle methods (start, stop, pause, resume)
- Common status and statistics tracking

### 3. Configuration Management
- Validation and updates
- Type-specific configuration examples
- Runtime configuration changes

### 4. Manager Integration
- Global crawler registry
- Batch operations
- Status monitoring

### 5. Error Handling
- Comprehensive error tracking
- Graceful failure handling
- Detailed error messages

## API Reference

### Core Classes

#### `CrawlerInterface`
Base interface that all crawlers must implement.

**Methods:**
- `async start(**kwargs) -> bool`
- `async stop() -> bool`
- `async pause() -> bool`
- `async resume() -> bool`
- `get_status() -> Dict[str, Any]`
- `async configure(config: Dict[str, Any]) -> bool`
- `async validate_config(config: Dict[str, Any]) -> bool`

#### `CrawlerFactory`
Factory class for creating crawler instances.

**Methods:**
- `create_crawler(type, name, config) -> CrawlerInterface`
- `register_crawler_type(type, class)`
- `get_supported_types() -> List[str]`

#### `CrawlerManager`
Manages multiple crawler instances.

**Methods:**
- `add_crawler(crawler)`
- `remove_crawler(name)`
- `get_crawler(name) -> CrawlerInterface`
- `list_crawlers() -> List[str]`
- `get_all_status() -> Dict[str, Dict[str, Any]]`

### Utility Functions

#### Factory Functions
- `create_scrapy_crawler_with_settings()`
- `create_selenium_crawler_with_options()`
- `create_and_register_crawler()`

#### Manager Functions
- `start_crawler_by_name(name)`
- `stop_crawler_by_name(name)`
- `pause_crawler_by_name(name)`
- `resume_crawler_by_name(name)`
- `get_crawler_status_by_name(name)`

#### Batch Operations
- `start_all_crawlers()`
- `stop_all_crawlers()`
- `get_all_crawler_statuses()`
- `get_running_crawler_names()`

## Examples

See `examples/usage_example.py` for comprehensive usage examples including:
- Basic crawler creation and management
- Custom crawler implementation
- Batch operations
- Error handling
- Configuration management

## Extension Guide

To add a new crawler type:

1. Create a new file in `implementations/`
2. Implement the `CrawlerInterface`
3. Register the crawler type with the factory
4. Add configuration examples
5. Update the `__init__.py` file

Example structure:
````python
# implementations/my_crawler.py
class MyCrawler(CrawlerInterface):
    # Implementation here
    pass

# Register the crawler
def register_my_crawler():
    from ..impl import CrawlerFactory
    CrawlerFactory.register_crawler_type('mycrawler', MyCrawler)

# Configuration example
MY_CRAWLER_CONFIG_EXAMPLE = {
    'param1': 'value1',
    'param2': 'value2'
}

# Convenience function
def create_my_crawler(name: str, **kwargs) -> MyCrawler:
    config = MY_CRAWLER_CONFIG_EXAMPLE.copy()
    config.update(kwargs)
    return MyCrawler(name, config)
```

## Testing

Run the examples to test the system:

```bash
# Run comprehensive usage example
python -m backend.src.crawlers.examples.usage_example

# Test individual components
python -m backend.src.crawlers.crawler_factory
python -m backend.src.crawlers.impl
```

## Dependencies

### Core Dependencies
- `asyncio` - Async/await support
- `logging` - Logging functionality
- `datetime` - Timestamp handling
- `typing` - Type hints

### Scrapy Crawler
- `scrapy` - Web scraping framework
- `twisted` - Async networking (Scrapy dependency)

### Selenium Crawler
- `selenium` - Browser automation
- `webdriver-manager` - WebDriver management (optional)

### API Crawler Example
- `aiohttp` - Async HTTP client

## Configuration Examples

### Production Scrapy Configuration
```python
PRODUCTION_SCRAPY_CONFIG = {
    'spider_name': 'production_spider',
    'settings': {
        'DOWNLOAD_DELAY': 2,
        'RANDOMIZE_DOWNLOAD_DELAY': 0.5,
        'CONCURRENT_REQUESTS': 8,
        'CONCURRENT_REQUESTS_PER_DOMAIN': 2,
        'ROBOTSTXT_OBEY': True,
        'USER_AGENT': 'MyBot 1.0 (+http://www.example.com/bot)',
        'AUTOTHROTTLE_ENABLED': True,
        'AUTOTHROTTLE_START_DELAY': 1,
        'AUTOTHROTTLE_MAX_DELAY': 60,
        'AUTOTHROTTLE_TARGET_CONCURRENCY': 1.0,
        'COOKIES_ENABLED': True,
        'TELNETCONSOLE_ENABLED': False,
        'DEFAULT_REQUEST_HEADERS': {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en',
        }
    }
}
```

### Production Selenium Configuration
```python
PRODUCTION_SELENIUM_CONFIG = {
    'driver_type': 'chrome',
    'headless': True,
    'timeout': 30,
    'window_size': (1920, 1080),
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'options': {
        'disable_images': True,
        'disable_javascript': False,
        'page_load_strategy': 'normal',
        'disable_extensions': True,
        'disable_plugins': True,
        'disable_dev_shm_usage': True,
        'no_sandbox': True  # For Docker environments
    }
}
```

## Best Practices

### 1. Error Handling
- Always implement proper error handling in custom crawlers
- Use the `_set_error()` method to record errors
- Log errors with appropriate levels

### 2. Resource Management
- Clean up resources in the `stop()` method
- Use context managers where appropriate
- Handle network timeouts gracefully

### 3. Configuration
- Validate configuration in `validate_config()`
- Provide sensible defaults
- Document configuration options

### 4. Performance
- Implement rate limiting for API crawlers
- Use appropriate concurrency settings
- Monitor resource usage

### 5. Monitoring
- Update statistics regularly
- Provide meaningful status information
- Log important events

## Troubleshooting

### Common Issues

#### 1. Crawler Won't Start
- Check configuration validation
- Verify required dependencies are installed
- Check error messages in logs

#### 2. Selenium Driver Issues
- Ensure WebDriver is installed and in PATH
- Check driver compatibility with browser version
- Verify headless mode settings

#### 3. Scrapy Spider Not Found
- Verify spider module path
- Check spider class name
- Ensure spider is properly registered

#### 4. Memory Issues
- Reduce concurrent requests
- Implement proper cleanup
- Monitor resource usage

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Performance Monitoring

Monitor crawler performance:
```python
# Get detailed status
status = crawler.get_status()
stats = status['stats']

print(f"Runtime: {stats['duration']} seconds")
print(f"Pages/second: {stats['pages_visited'] / stats['duration']}")
print(f"Items/second: {stats['items_scraped'] / stats['duration']}")
print(f"Error rate: {stats['errors_count'] / stats['pages_visited'] * 100}%")
```

## Future Enhancements

### Planned Features
- Database integration for crawler state persistence
- Distributed crawling support
- Web UI for crawler management
- Advanced scheduling and queuing
- Metrics and monitoring dashboard
- Plugin system for custom extensions

### Contributing

To contribute to the crawler system:

1. Follow the existing code structure
2. Implement comprehensive tests
3. Document new features
4. Follow Python coding standards
5. Add type hints
6. Include usage examples

## License

This crawler system is part of the larger project and follows the same licensing terms.
