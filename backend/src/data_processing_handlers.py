import logging
import numpy as np

from src.db import insert_web_page
from src.embeddings import create_embedding_with_ollama, truncate_or_pad_vector, normalize
from src.rabbitmq_events import event_manager, CrawlerEvent

logger = logging.getLogger(__name__)

def handle_page_processed(data: dict):
    """
    Handles the PAGE_PROCESSED event.
    Generates embeddings and inserts the page data into the database.
    """
    url = data.get("url")
    full_text = data.get("content")

    if not url or not full_text:
        logger.error("Received PAGE_PROCESSED event with missing URL or content.")
        return

    logger.info(f"Processing page for embedding and insertion: {url}")

    try:
        embedding = create_embedding_with_ollama(full_text)
        embedding = normalize(embedding)
        embedding = truncate_or_pad_vector(embedding, dims=1024)

        page_data = {
            "url": url,
            "title": data.get("title"),
            "meta_description": data.get("meta_description"),
            "meta_tags": data.get("meta_tags"),
            "content": full_text,
            "embedding": embedding,
        }

        insert_web_page(page_data)
        logger.info(f"Successfully inserted page: {url}")

    except Exception as e:
        logger.error(f"Failed to process and insert page {url}: {e}", exc_info=True)
        # In a production system, you might want to re-queue the message
        # or send it to a dead-letter queue for later inspection.
        raise # Re-raising will cause Pika to nack and requeue the message

def setup_data_processing_handlers():
    """Registers event handlers for data processing."""
    event_manager.register_event_handler(CrawlerEvent.PAGE_PROCESSED, handle_page_processed)
    logger.info("Data processing handlers registered.")
