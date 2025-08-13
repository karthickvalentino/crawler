import logging
import subprocess
import sys

logger = logging.getLogger(__name__)

def run_scrapy_crawl(start_urls: list, allowed_domains: list, depth_limit: int):
    """
    Configures and runs a Scrapy crawl in a separate process using subprocess.
    """
    logger.info(
        f"Starting Scrapy crawl in a subprocess with start_urls={start_urls}, "
        f"allowed_domains={allowed_domains}, depth_limit={depth_limit}"
    )

    command = [
        sys.executable,  # Use the same python interpreter
        "-m", "src.crawlers.scrapy_runner",
        "--start_urls", *start_urls,
        "--allowed_domains", *allowed_domains,
        "--depth_limit", str(depth_limit),
    ]

    try:
        # We use subprocess.run which is a blocking call.
        # It will wait for the crawl to complete.
        result = subprocess.run(
            command,
            check=True,  # Raise an exception if the command returns a non-zero exit code
            capture_output=True,  # Capture stdout and stderr
            text=True,  # Decode stdout/stderr as text
        )
        logger.info("Scrapy subprocess finished successfully.")
        logger.info(f"Subprocess stdout:\n{result.stdout}")
        if result.stderr:
            logger.warning(f"Subprocess stderr:\n{result.stderr}")

    except subprocess.CalledProcessError as e:
        logger.error(f"Scrapy subprocess failed with exit code {e.returncode}.")
        logger.error(f"Subprocess stdout:\n{e.stdout}")
        logger.error(f"Subprocess stderr:\n{e.stderr}")
        # Re-raise the exception to let Celery handle the task failure
        raise e

    except FileNotFoundError:
        logger.error(f"Could not find the python interpreter at {sys.executable} or the runner script.")
        raise
