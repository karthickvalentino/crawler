import json


import scrapy
import numpy as np


from src.db import insert_web_page
from src.embeddings import create_embedding_with_ollama, truncate_or_pad_vector, normalize
from scrapy.utils.reactor import install_reactor
# install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")






class DynamicSpider(scrapy.Spider):
    name = "dynamic_spider"

    def __init__(self, start_url=None, custom_flags={}, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # install_reactor("twisted.internet.asyncioreactor.AsyncioSelectorReactor")
        self.start_urls = [start_url]
        self.allowed_domains = [start_url.split("//")[-1].split("/")[0]]
        self.custom_flags = custom_flags
        

    def parse(self, response):
        # Extract meta tags as a dictionary
        print("starting parse")
        meta_tags = {
            meta.attrib.get("name") or meta.attrib.get("property"): meta.attrib.get("content")
            for meta in response.xpath("//meta[@name or @property]")
            if meta.attrib.get("content") is not None
        }

        # result = {
        #     "url": response.url,
        #     "title": response.xpath("//title/text()").get(),
        #     "meta": meta_tags,
        #     "body": response.xpath("//body//text()").getall()
        # }

        # yield result

        print("url", response.url)

        title = response.xpath("//title/text()").get()
        meta_desc = response.xpath("//meta[@name='description']/@content").get()
        headings = response.xpath("//h1/text() | //h2/text() | //h3/text() | //h4/text()").getall()
        main = response.xpath("//main//text()").getall()
        section = response.xpath("//section//text()").getall()
        paragraphs = response.xpath("//p//text()").getall()
        # body = response.xpath("//body//text()").getall()
        body_text = response.xpath(
            "//body//*[not(self::script or self::style or self::noscript or self::template or self::svg)]/text()[normalize-space()]"
        ).getall()

        content_pieces = [
            f"Title: {title}",
            # f"Meta Description: {meta_desc}",
            "Headings: " + " | ".join(headings),
            # "Main: " + " ".join(main),
            "Section: " + " ".join(section),
            "Paragraphs: " + " ".join(paragraphs),
            "Body: " + " ".join(t.strip() for t in body_text if t.strip())
        ]

        full_text = "\n".join([piece for piece in content_pieces if piece])
        full_text = full_text.strip()

        print("text", full_text)

        embedding = create_embedding_with_ollama(full_text)
        print(f"Embedding shape: {np.array(embedding).shape}")
        embedding = normalize(embedding)
        embedding = truncate_or_pad_vector(embedding, dims=1024)
        print(f"Reduced embedding shape: {np.array(embedding).shape}")
        print(f"Embedding: {embedding}")
        

        page_data = {
            "url": response.url,
            "title": title,
            "meta_description": meta_desc,
            "meta_tags": meta_tags,
            "content": full_text,
            "embedding": embedding,
        }
        print(f"Inserting {response.url}")
        insert_web_page(page_data)
        print(f"Inserted {response.url}")

        for href in response.css("a::attr(href)").getall():
            url = response.urljoin(href)
            if self.allowed_domains[0] in url:
                yield scrapy.Request(url, callback=self.parse)
