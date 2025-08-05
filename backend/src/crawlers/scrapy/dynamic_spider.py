import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class DynamicCrawlSpider(CrawlSpider):
    name = "dynamic_crawler"

    def __init__(self, *args, **kwargs):
        # We will get start_urls and allowed_domains from the kwargs
        self.start_urls = kwargs.get('start_urls', [])
        self.allowed_domains = kwargs.get('allowed_domains', [])
        
        # Dynamically create rules for the link extractor
        DynamicCrawlSpider.rules = (
            Rule(
                LinkExtractor(allow_domains=self.allowed_domains),
                callback='parse_item',
                follow=True
            ),
        )
        
        super(DynamicCrawlSpider, self).__init__(*args, **kwargs)

    def parse_item(self, response):
        """
        This method is called for each page crawled.
        It extracts data and yields an item.
        """
        self.logger.info(f"Parsing page: {response.url}")

        meta_tags = {
            meta.attrib.get("name") or meta.attrib.get("property"): meta.attrib.get("content")
            for meta in response.xpath("//meta[@name or @property]")
            if meta.attrib.get("content") is not None
        }

        title = response.xpath("//title/text()").get()
        meta_desc = response.xpath("//meta[@name='description']/@content").get()
        
        # A more robust way to get all text content, excluding scripts/styles
        body_text = response.xpath(
            "//body//*[not(self::script or self::style or self::noscript or self::template or self::svg)]/text()[normalize-space()]"
        ).getall()

        full_text = " ".join(t.strip() for t in body_text if t.strip())

        # Yield a dictionary (which acts as a Scrapy Item)
        # This will be caught by the CeleryPipeline
        yield {
            "url": response.url,
            "title": title,
            "meta_description": meta_desc,
            "meta_tags": meta_tags,
            "content": full_text,
        }