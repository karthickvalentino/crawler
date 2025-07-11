"""
Content processing handlers for embedding creation and database storage
"""

import asyncio
import logging
import numpy as np
from typing import Dict, Any, List
from datetime import datetime
import hashlib
import json

from .content_events import (
    ContentEvent,
    publish_content_event,
    register_content_event_handler
)

from src.db import insert_web_page
from src.embeddings import create_embedding_with_ollama, truncate_or_pad_vector, normalize

logger = logging.getLogger(__name__)

class ContentProcessor:
    """Handles content processing operations"""
    
    def __init__(self):
        self.processing_stats = {
            'scraped_count': 0,
            'embedding_requests': 0,
            'embeddings_created': 0,
            'embeddings_failed': 0,
            'content_stored': 0,
            'storage_failed': 0
        }
        self.batch_buffer = []
        self.batch_size = int(os.getenv('CONTENT_BATCH_SIZE', '10'))
        self.batch_timeout = int(os.getenv('CONTENT_BATCH_TIMEOUT', '30'))  # seconds
        
    def generate_content_id(self, url: str, content: str) -> str:
        """Generate a unique ID for content"""
        content_hash = hashlib.sha256(f"{url}:{content}".encode()).hexdigest()
        return f"content_{content_hash[:16]}"
    
    def handle_scraped_content(self, data: Dict[str, Any]):
        """Handle scraped content event - request embedding creation"""
        try:
            logger.info(f"Processing scraped content from: {data.get('url')}")
            
            # Update stats
            self.processing_stats['scraped_count'] += 1
            
            # Generate content ID
            content_id = self.generate_content_id(data.get('url', ''), data.get('content', ''))
            
            # Add content ID to data
            data['content_id'] = content_id
            data['processed_at'] = datetime.now().isoformat()
            
            # Validate required fields
            required_fields = ['url', 'content']
            missing_fields = [field for field in required_fields if not data.get(field)]
            
            if missing_fields:
                logger.error(f"Missing required fields for content processing: {missing_fields}")
                return
            
            # Check if we should process immediately or batch
            batch_processing = data.get('batch_processing', False)
            
            if batch_processing:
                # Add to batch buffer
                self.batch_buffer.append(data)
                logger.info(f"Added content to batch buffer. Buffer size: {len(self.batch_buffer)}")
                
                # Process batch if buffer is full
                if len(self.batch_buffer) >= self.batch_size:
                    self._process_batch()
            else:
                # Process immediately
                self._request_embedding(data)
                
        except Exception as e:
            logger.error(f"Error handling scraped content: {str(e)}")
    
    def _request_embedding(self, data: Dict[str, Any]):
        """Request embedding creation for content"""
        try:
            # Publish embedding request event
            embedding_data = {
                'content_id': data['content_id'],
                'url': data['url'],
                'content': data['content'],
                'title': data.get('title'),
                'meta_description': data.get('meta_description'),
                'meta_tags': data.get('meta_tags', {}),
                'crawler_job_id': data.get('crawler_job_id'),
                'requested_at': datetime.now().isoformat()
            }
            
            success = publish_content_event(ContentEvent.EMBEDDING_REQUESTED, embedding_data)
            
            if success:
                self.processing_stats['embedding_requests'] += 1
                logger.info(f"Requested embedding for content: {data['content_id']}")
            else:
                logger.error(f"Failed to request embedding for content: {data['content_id']}")
                
        except Exception as e:
            logger.error(f"Error requesting embedding: {str(e)}")
    
    def _process_batch(self):
        """Process batch of content items"""
        try:
            if not self.batch_buffer:
                return
            
            logger.info(f"Processing batch of {len(self.batch_buffer)} content items")
            
            # Publish batch processing event
            batch_data = {
                'batch_id': f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'items': self.batch_buffer.copy(),
                'batch_size': len(self.batch_buffer),
                'created_at': datetime.now().isoformat()
            }
            
            success = publish_content_event(ContentEvent.BATCH_PROCESS_CONTENT, batch_data)
            
            if success:
                logger.info(f"Published batch processing event for {len(self.batch_buffer)} items")
                self.batch_buffer.clear()
            else:
                logger.error("Failed to publish batch processing event")
                
        except Exception as e:
            logger.error(f"Error processing batch: {str(e)}")
    
    def handle_embedding_request(self, data: Dict[str, Any]):
        """Handle embedding creation request"""
        try:
            content_id = data.get('content_id')
            content = data.get('content')
            
            logger.info(f"Creating embedding for content: {content_id}")
            
            if not content:
                logger.error(f"No content provided for embedding: {content_id}")
                self._publish_embedding_failed(data, "No content provided")
                return
            
            # Create embedding
            try:
                embedding = create_embedding_with_ollama(content)
                logger.debug(f"Raw embedding shape: {np.array(embedding).shape}")
                
                # Normalize and truncate embedding
                embedding = normalize(embedding)
                embedding = truncate_or_pad_vector(embedding, dims=1024)
                
                logger.debug(f"Processed embedding shape: {np.array(embedding).shape}")
                
                # Prepare embedding data
                embedding_data = data.copy()
                embedding_data.update({
                    'embedding': embedding.tolist() if isinstance(embedding, np.ndarray) else embedding,
                    'embedding_created_at': datetime.now().isoformat(),
                    'embedding_dimensions': len(embedding)
                })
                
                # Publish embedding created event
                success = publish_content_event(ContentEvent.EMBEDDING_CREATED, embedding_data)
                
                if success:
                    self.processing_stats['embeddings_created'] += 1
                    logger.info(f"Successfully created embedding for: {content_id}")
                else:
                    logger.error(f"Failed to publish embedding created event for: {content_id}")
                    self._publish_embedding_failed(data, "Failed to publish embedding event")
                    
            except Exception as e:
                logger.error(f"Error creating embedding for {content_id}: {str(e)}")
                self._publish_embedding_failed(data, str(e))
                
        except Exception as e:
            logger.error(f"Error handling embedding request: {str(e)}")
    
    def _publish_embedding_failed(self, data: Dict[str, Any], error_message: str):
        """Publish embedding failed event"""
        try:
            failed_data = data.copy()
            failed_data.update({
                'error_message': error_message,
                'failed_at': datetime.now().isoformat()
            })
            
            publish_content_event(ContentEvent.EMBEDDING_FAILED, failed_data)
            self.processing_stats['embeddings_failed'] += 1
            
        except Exception as e:
            logger.error(f"Error publishing embedding failed event: {str(e)}")
    
    def handle_embedding_created(self, data: Dict[str, Any]):
        """Handle embedding created event - store content in database"""
        try:
            content_id = data.get('content_id')
            logger.info(f"Storing content with embedding: {content_id}")
            
            # Prepare page data for database
            page_data = {
                "url": data.get('url'),
                "title": data.get('title'),
                "meta_description": data.get('meta_description'),
                "meta_tags": data.get('meta_tags', {}),
                "content": data.get('content'),
                "embedding": data.get('embedding'),
                "content_id": content_id,
                "crawler_job_id": data.get('crawler_job_id'),
                "processed_at": data.get('embedding_created_at')
            }
            
            # Insert into database
            try:
                insert_web_page(page_data)
                
                # Publish storage success event
                storage_data = {
                    'content_id': content_id,
                    'url': data.get('url'),
                    'stored_at': datetime.now().isoformat(),
                    'crawler_job_id': data.get('crawler_job_id')
                }
                
                publish_content_event(ContentEvent.CONTENT_STORED, storage_data)
                self.processing_stats['content_stored'] += 1
                
                logger.info(f"Successfully stored content: {content_id}")
                
            except Exception as e:
                logger.error(f"Error storing content {content_id}: {str(e)}")
                self._publish_storage_failed(data, str(e))
                
        except Exception as e:
            logger.error(f"Error handling embedding created event: {str(e)}")
    
    def _publish_storage_failed(self, data: Dict[str, Any], error_message: str):
        """Publish storage failed event"""
        try:
            failed_data = {
                'content_id': data.get('content_id'),
                'url': data.get('url'),
                'error_message': error_message,
                'failed_at': datetime.now().isoformat(),
                'crawler_job_id': data.get('crawler_job_id')
            }
            
            publish_content_event(ContentEvent.CONTENT_STORAGE_FAILED, failed_data)
            self.processing_stats['storage_failed'] += 1
            
        except Exception as e:
            logger.error(f"Error publishing storage failed event: {str(e)}")
    
    def handle_embedding_failed(self, data: Dict[str, Any]):
        """Handle embedding failed event"""
        content_id = data.get('content_id')
        error_message = data.get('error_message', 'Unknown error')
        
        logger.error(f"Embedding failed for content {content_id}: {error_message}")
        
        # Could implement retry logic here
        # For now, just log the failure
    
    def handle_storage_failed(self, data: Dict[str, Any]):
        """Handle storage failed event"""
        content_id = data.get('content_id')
        error_message = data.get('error_message', 'Unknown error')
        
        logger.error(f"Storage failed for content {content_id}: {error_message}")
        
        # Could implement retry logic here
        # For now, just log the failure
    
    def handle_batch_processing(self, data: Dict[str, Any]):
        """Handle batch processing event"""
        try:
            batch_id = data.get('batch_id')
            items = data.get('items', [])
            
            logger.info(f"Processing batch {batch_id} with {len(items)} items")
            
            # Process each item in the batch
            for item in items:
                try:
                    self._request_embedding(item)
                except Exception as e:
                    logger.error(f"Error processing batch item: {str(e)}")
            
            logger.info(f"Completed batch processing for {batch_id}")
            
        except Exception as e:
            logger.error(f"Error handling batch processing: {str(e)}")
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """Get current processing statistics"""
        return {
            **self.processing_stats,
            'batch_buffer_size': len(self.batch_buffer),
            'timestamp': datetime.now().isoformat()
        }

# Global content processor instance
content_processor = ContentProcessor()

def setup_content_processors():
    """Setup all content processing event handlers"""
    
    # Register event handlers
    register_content_event_handler(
        ContentEvent.CONTENT_SCRAPED, 
        content_processor.handle_scraped_content
    )
    
    register_content_event_handler(
        ContentEvent.EMBEDDING_REQUESTED, 
        content_processor.handle_embedding_request
    )
    
    register_content_event_handler(
        ContentEvent.EMBEDDING_CREATED, 
        content_processor.handle_embedding_created
    )
    
    register_content_event_handler(
        ContentEvent.EMBEDDING_FAILED, 
        content_processor.handle_embedding_failed
    )
    
    register_content_event_handler(
        ContentEvent.CONTENT_STORED, 
        lambda data: logger.info(f"Content stored successfully: {data.get('content_id')}")
    )
    
    register_content_event_handler(
        ContentEvent.CONTENT_STORAGE_FAILED, 
        content_processor.handle_storage_failed
    )
    
    register_content_event_handler(
        ContentEvent.BATCH_PROCESS_CONTENT, 
        content_processor.handle_batch_processing
    )
    
    logger.info("Content processing event handlers registered successfully")

def get_content_processing_stats() -> Dict[str, Any]:
    """Get content processing statistics"""
    return content_processor.get_processing_stats()