import unittest
from unittest.mock import MagicMock, patch

from src.crawlers.scrapy.pipelines import CeleryPipeline

class TestCeleryPipeline(unittest.TestCase):

    @patch('src.crawlers.scrapy.pipelines.process_page_data_task.delay')
    def test_process_item_sends_to_celery(self, mock_delay):
        # Arrange
        pipeline = CeleryPipeline()
        item = {"url": "http://example.com", "content": "some content"}
        spider = MagicMock()

        # Act
        result = pipeline.process_item(item, spider)

        # Assert
        mock_delay.assert_called_once_with(dict(item))
        self.assertEqual(result, item)

if __name__ == '__main__':
    unittest.main()
