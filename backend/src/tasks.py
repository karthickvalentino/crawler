import logging
from uuid import UUID

from src.celery_app import celery_app
from src.crawlers.crawler_factory import run_scrapy_crawl
from src.db import insert_web_page, update_job
from src.embeddings import (
    create_embedding_with_ollama,
    create_multimodal_embedding_with_ollama,
    normalize,
    truncate_or_pad_vector,
)
from src.models import JobUpdate

logger = logging.getLogger(__name__)

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True
)
def run_crawler_task(self, job_id: str, domain: str, depth: int, flags: dict):
    """
    Celery task to run a crawler for a given domain.
    """
    try:
        logger.info(f"Starting crawler for job_id: {job_id}, domain: {domain}")
        update_job(UUID(job_id), JobUpdate(status='running'))

        run_scrapy_crawl(
            start_urls=[f"https://{domain}"],
            allowed_domains=[domain],
            depth_limit=depth
        )
        
        update_job(UUID(job_id), JobUpdate(status='completed'))
        logger.info(f"Crawler finished for job_id: {job_id}")

    except Exception as e:
        logger.error(f"Crawler task failed for job_id: {job_id}: {e}", exc_info=True)
        update_job(UUID(job_id), JobUpdate(status='failed', result={"error": str(e)}))
        raise

@celery_app.task(
    bind=True,
    autoretry_for=(Exception,),
    retry_kwargs={'max_retries': 3, 'countdown': 60},
    acks_late=True
)
def process_page_data_task(self, page_data: dict):
    """
    Celery task to process a single page's data: generate embeddings and save to DB.
    """
    url = page_data.get("url")
    content = page_data.get("content")
    file_type = page_data.get("file_type", "html")
    embedding_type = page_data.get("embedding_type", "text")

    if not url:
        logger.error("Received page data with missing URL.")
        return
    
    if not content and file_type not in ["image"]:
        logger.error(f"Received page data with missing content for file type {file_type}.")
        return

    logger.info(f"Processing {file_type} for embedding and insertion: {url}")

    try:
        if embedding_type == "text":
            embedding = create_embedding_with_ollama(content)
        elif embedding_type == "vision":
            embedding = create_multimodal_embedding_with_ollama(url)
        else:
            embedding = None

        if embedding:
            embedding = normalize(embedding)
            embedding = truncate_or_pad_vector(embedding, dims=1024)

        db_page_data = {
            "url": url,
            "title": page_data.get("title"),
            "meta_description": page_data.get("meta_description"),
            "meta_tags": page_data.get("meta_tags"),
            "content": content,
            "embedding": embedding,
            "file_type": file_type,
            "embedding_type": embedding_type,
        }

        insert_web_page(db_page_data)
        logger.info(f"Successfully inserted page: {url}")

    except Exception as e:
        logger.error(f"Failed to process and insert page {url}: {e}", exc_info=True)
        raise

