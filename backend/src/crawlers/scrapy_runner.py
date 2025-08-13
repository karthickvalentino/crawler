
import argparse
import logging
import sys

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings
from src.crawlers.scrapy.dynamic_spider import DynamicCrawlSpider

# Add the project root to the Python path
sys.path.append('.')

logger = logging.getLogger(__name__)

def run_crawl(start_urls: list, allowed_domains: list, depth_limit: int):
    """
    Configures and runs a Scrapy crawl.
    """
    settings = Settings()
    settings.setmodule("src.crawlers.scrapy.settings")
    settings.set("DEPTH_LIMIT", depth_limit)

    process = CrawlerProcess(settings)
    process.crawl(
        DynamicCrawlSpider, start_urls=start_urls, allowed_domains=allowed_domains
    )
    process.start()  # This is a blocking call

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a Scrapy crawl.")
    parser.add_argument("--start_urls", nargs="+", required=True, help="List of starting URLs.")
    parser.add_argument("--allowed_domains", nargs="+", required=True, help="List of allowed domains.")
    parser.add_argument("--depth_limit", type=int, default=1, help="Crawling depth limit.")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)
    logger.info(
        f"Starting Scrapy runner with start_urls={args.start_urls}, "
        f"allowed_domains={args.allowed_domains}, depth_limit={args.depth_limit}"
    )
    
    run_crawl(args.start_urls, args.allowed_domains, args.depth_limit)
    
    logger.info("Scrapy runner finished.")
