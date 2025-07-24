import scrapy
from src.rabbitmq_events import event_manager, CrawlerEvent

class DynamicSpider(scrapy.Spider):
    name = "dynamic_spider"

    def __init__(self, start_url=None, custom_flags={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.start_urls = [start_url]
        self.allowed_domains = [start_url.split("//")[-1].split("/")[0]]
        self.custom_flags = custom_flags

    def parse(self, response):
        self.logger.info(f"Parsing page: {response.url}")
        meta_tags = {
            meta.attrib.get("name") or meta.attrib.get("property"): meta.attrib.get("content")
            for meta in response.xpath("//meta[@name or @property]")
            if meta.attrib.get("content") is not None
        }

        title = response.xpath("//title/text()").get()
        meta_desc = response.xpath("//meta[@name='description']/@content").get()
        headings = response.xpath("//h1/text() | //h2/text() | //h3/text() | //h4/text()").getall()
        main = response.xpath("//main//text()").getall()
        section = response.xpath("//section//text()").getall()
        paragraphs = response.xpath("//p//text()").getall()
        body_text = response.xpath(
            "//body//*[not(self::script or self::style or self::noscript or self::template or self::svg)]/text()[normalize-space()]"
        ).getall()

        content_pieces = [
            f"Title: {title}",
            "Headings: " + " | ".join(headings),
            "Section: " + " ".join(section),
            "Paragraphs: " + " ".join(paragraphs),
            "Body: " + " ".join(t.strip() for t in body_text if t.strip())
        ]

        full_text = "\n".join([piece for piece in content_pieces if piece]).strip()

        page_data = {
            "url": response.url,
            "title": title,
            "meta_description": meta_desc,
            "meta_tags": meta_tags,
            "content": full_text,
        }

        # Publish event for async processing
        event_manager.publish_event(
            CrawlerEvent.PAGE_PROCESSED,
            page_data,
            routing_key='crawler.data.page_processed'
        )
        self.logger.info(f"Published PAGE_PROCESSED event for {response.url}")

        # Follow links
        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            if self.allowed_domains[0] in url:
                yield scrapy.Request(url, callback=self.parse)

