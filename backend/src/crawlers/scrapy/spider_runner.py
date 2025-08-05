from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from src.crawlers.scrapy.dynamic_spider import DynamicCrawlSpider

def run_crawler(url, depth=1, output="output.json", custom_flags=None):

    settings = get_project_settings()
    # settings.set("FEED_FORMAT", "json")
    # settings.set("FEED_URI", output)
    settings.set("DEPTH_LIMIT", depth)
    settings.set("LOG_ENABLED", False)

    process = CrawlerProcess(settings)
    process.crawl(DynamicCrawlSpider, start_url=url, custom_flags=custom_flags or {})
    process.start()