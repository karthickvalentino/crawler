import logging

from scrapy.crawler import CrawlerProcess
from scrapy.settings import Settings

from .scrapy.dynamic_spider import DynamicCrawlSpider

logger = logging.getLogger(__name__)


def run_scrapy_crawl(start_urls: list, allowed_domains: list, depth_limit: int):
    """
    Configures and runs a Scrapy crawl for the given parameters.
    This function will block until the crawl is finished.
    """
    settings = Settings()
    settings.setmodule("src.crawlers.scrapy.settings")
    settings.set("DEPTH_LIMIT", depth_limit)

    process = CrawlerProcess(settings)

    logger.info(
        f"Starting Scrapy crawl with start_urls={start_urls}, "
        f"allowed_domains={allowed_domains}, depth_limit={depth_limit}"
    )

    process.crawl(
        DynamicCrawlSpider, start_urls=start_urls, allowed_domains=allowed_domains
    )

    # The script will block here until the crawling is finished
    process.start()

    logger.info("Scrapy crawl finished.")
