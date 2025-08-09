import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from src.crawlers.file_handler import handle_pdf, handle_image

class DynamicCrawlSpider(CrawlSpider):
    name = "dynamic_crawler"

    def __init__(self, *args, **kwargs):
        self.start_urls = kwargs.get('start_urls', [])
        self.allowed_domains = kwargs.get('allowed_domains', [])
        
        DynamicCrawlSpider.rules = (
            Rule(
                LinkExtractor(
                    allow_domains=self.allowed_domains,
                    allow=(),
                    deny_extensions=[], # Let the content type check handle it
                    tags=('a', 'img'),  # Look at both anchor and image tags
                    attrs=('href', 'src'), # Extract from href and src attributes
                ),
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
        content_type = response.headers.get('Content-Type', b'').decode('utf-8').lower()

        if 'application/pdf' in content_type:
            self.logger.info(f"Processing PDF: {response.url}")
            pdf_data = handle_pdf(response.url)
            if pdf_data:
                yield pdf_data
        elif 'image/' in content_type:
            self.logger.info(f"Processing image: {response.url}")
            image_data = handle_image(response.url)
            if image_data:
                yield image_data
        elif 'text/html' in content_type:
            self.logger.info(f"Parsing page: {response.url}")
            yield self.parse_html(response)
        else:
            self.logger.info(f"Skipping content type: {content_type} at {response.url}")


    def parse_html(self, response):
        meta_tags = {
            meta.attrib.get("name") or meta.attrib.get("property"): meta.attrib.get("content")
            for meta in response.xpath("//meta[@name or @property]")
            if meta.attrib.get("content") is not None
        }

        title = response.xpath("//title/text()").get()
        meta_desc = response.xpath("//meta[@name='description']/@content").get()
        
        body_text = response.xpath(
            "//body//*[not(self::script or self::style or self::noscript or self::template or self::svg)]/text()[normalize-space()]"
        ).getall()

        full_text = " ".join(t.strip() for t in body_text if t.strip())

        return {
            "url": response.url,
            "title": title,
            "meta_description": meta_desc,
            "meta_tags": meta_tags,
            "content": full_text,
            "file_type": "html",
            "embedding_type": "text",
        }


