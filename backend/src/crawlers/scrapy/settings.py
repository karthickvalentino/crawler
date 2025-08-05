BOT_NAME = "scrapy_project"

SPIDER_MODULES = ["src.crawlers.scrapy"]
NEWSPIDER_MODULE = "src.crawlers.scrapy"

# Obey robots.txt rules
ROBOTSTXT_OBEY = True

# Set a default depth limit
DEPTH_LIMIT = 1

# Configure a default user agent
USER_AGENT = 'Mozilla/5.0 (compatible; MyCrawler/1.0; +http://www.example.com)'

# Configure item pipelines
ITEM_PIPELINES = {
   'src.crawlers.scrapy.pipelines.CeleryPipeline': 300,
}
