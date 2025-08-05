import logging
from src.tasks import process_page_data_task

logger = logging.getLogger(__name__)

class CeleryPipeline:
    """
    A Scrapy pipeline that sends each scraped item to a Celery task for processing.
    """
    def process_item(self, item, spider):
        """
        This method is called for every item pipeline component.
        """
        logger.info(f"Sending item to Celery task: {item.get('url')}")
        try:
            # Convert the Scrapy item to a dictionary and send it to the Celery task
            process_page_data_task.delay(dict(item))
        except Exception as e:
            logger.error(f"Failed to send item to Celery task: {e}", exc_info=True)
        return item
