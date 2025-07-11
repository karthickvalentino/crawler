BOT_NAME = "scrapy_project"

SPIDER_MODULES = ["src.scrapy_project.spiders"]
NEWSPIDER_MODULE = "src.scrapy_project.spiders"

ROBOTSTXT_OBEY = True
DEPTH_LIMIT = 1  # Can be overridden from app
