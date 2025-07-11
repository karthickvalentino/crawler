"""
RabbitMQ Event System for Crawler Management
Handles publishing and consuming crawler events
"""

import pika
import json
import logging
import os
import threading
import time
from typing import Dict, Any, Callable, Optional
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)

class CrawlerEvent(Enum):
    """Crawler event types"""
    START_CRAWLER = "start_crawler"
    STOP_CRAWLER = "stop_crawler"
    PAUSE_CRAWLER = "pause_crawler"
    RESUME_CRAWLER = "resume_crawler"
    CRAWLER_STARTED = "crawler_started"
    CRAWLER_STOPPED = "crawler_stopped"
    CRAWLER_PAUSED = "crawler_paused"
    CRAWLER_RESUMED = "crawler_resumed"
    CRAWLER_COMPLETED = "crawler_completed"
    CRAWLER_FAILED = "crawler_failed"
    CRAWLER_PROGRESS = "crawler_progress"
    CRAWLER_ERROR = "crawler_error"

class RabbitMQEventManager:
    """Manages RabbitMQ connections and event publishing/consuming"""
    
    def __init__(self, 
                 host: str = None,
                 port: int = None,
                 username: str = None,
                 password: str = None,
                 virtual_host: str = None):
        
        # Get connection parameters from environment or use defaults
        self.host = host or os.getenv('RABBITMQ_HOST', 'localhost')
        self.port = port or int(os.getenv('RABBITMQ_PORT', '5672'))
        self.username = username or os.getenv('RABBITMQ_USERNAME', 'crawler_user')
        self.password = password or os.getenv('RABBITMQ_PASSWORD', 'crawler_pass')
        self.virtual_host = virtual_host or os.getenv('RABBITMQ_VHOST', 'crawler_vhost')
        
        # Connection and channel
        self.connection = None
        self.channel = None
        self.consuming = False
        self.consumer_thread = None
        
        # Event handlers
        self.event_handlers: Dict[str, Callable] = {}
        
        # Queue and exchange names
        self.crawler_exchange = 'crawler_events'
        self.crawler_queue = 'crawler_commands'
        self.status_queue = 'crawler_status'
        
        logger.info(f"Initialized RabbitMQ Event Manager for {self.host}:{self.port}")
    
    def connect(self) -> bool:
        """Establish connection to RabbitMQ"""
        try:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300
            )
            
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()
            
            # Declare exchange
            self.channel.exchange_declare(
                exchange=self.crawler_exchange,
                exchange_type='topic',
                durable=True
            )
            
            # Declare queues
            self.channel.queue_declare(queue=self.crawler_queue, durable=True)
            self.channel.queue_declare(queue=self.status_queue, durable=True)
            
            # Bind queues to exchange
            self.channel.queue_bind(
                exchange=self.crawler_exchange,
                queue=self.crawler_queue,
                routing_key='crawler.command.*'
            )
            
            self.channel.queue_bind(
                exchange=self.crawler_exchange,
                queue=self.status_queue,
                routing_key='crawler.status.*'
            )
            
            logger.info("Connected to RabbitMQ successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {str(e)}")
            return False
    
    def disconnect(self):
        """Close RabbitMQ connection"""
        try:
            self.consuming = False
            if self.consumer_thread and self.consumer_thread.is_alive():
                self.consumer_thread.join(timeout=5)
            
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                logger.info("Disconnected from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting from RabbitMQ: {str(e)}")
    
    def publish_event(self, event_type: CrawlerEvent, data: Dict[str, Any], routing_key: str = None) -> bool:
        """Publish an event to RabbitMQ"""
        try:
            if not self.connection or self.connection.is_closed:
                if not self.connect():
                    return False
            
            # Prepare message
            message = {
                'event_type': event_type.value,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }
            
            # Determine routing key
            if not routing_key:
                if event_type in [CrawlerEvent.START_CRAWLER, CrawlerEvent.STOP_CRAWLER, 
                                CrawlerEvent.PAUSE_CRAWLER, CrawlerEvent.RESUME_CRAWLER]:
                    routing_key = f'crawler.command.{event_type.value}'
                else:
                    routing_key = f'crawler.status.{event_type.value}'
            
            # Publish message
            self.channel.basic_publish(
                exchange=self.crawler_exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    timestamp=int(time.time())
                )
            )
            
            logger.debug(f"Published event: {event_type.value} with routing key: {routing_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to publish event {event_type.value}: {str(e)}")
            return False
    
    def register_event_handler(self, event_type: CrawlerEvent, handler: Callable):
        """Register an event handler for a specific event type"""
        self.event_handlers[event_type.value] = handler
        logger.info(f"Registered handler for event: {event_type.value}")
    
    def _handle_message(self, channel, method, properties, body):
        """Handle incoming RabbitMQ message"""
        try:
            # Parse message
            message = json.loads(body.decode('utf-8'))
            event_type = message.get('event_type')
            data = message.get('data', {})
            timestamp = message.get('timestamp')
            
            logger.debug(f"Received event: {event_type} at {timestamp}")
            
            # Call appropriate handler
            if event_type in self.event_handlers:
                try:
                    self.event_handlers[event_type](data)
                    # Acknowledge message
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    logger.debug(f"Successfully handled event: {event_type}")
                except Exception as e:
                    logger.error(f"Error handling event {event_type}: {str(e)}")
                    # Reject message and requeue
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                logger.warning(f"No handler registered for event: {event_type}")
                # Acknowledge to remove from queue
                channel.basic_ack(delivery_tag=method.delivery_tag)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            # Reject message
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start consuming messages from RabbitMQ"""
        def consume():
            try:
                if not self.connection or self.connection.is_closed:
                    if not self.connect():
                        return
                
                # Set up consumer
                self.channel.basic_qos(prefetch_count=1)
                self.channel.basic_consume(
                    queue=self.crawler_queue,
                    on_message_callback=self._handle_message
                )
                
                logger.info("Started consuming crawler events")
                self.consuming = True
                
                # Start consuming
                while self.consuming:
                    try:
                        self.connection.process_data_events()
                    except Exception as e:
                        logger.error(f"Error processing events: {str(e)}")
                        time.sleep(1)
                        
            except Exception as e:
                logger.error(f"Error in consumer thread: {str(e)}")
        
        # Start consumer in separate thread
        self.consumer_thread = threading.Thread(target=consume, daemon=True)
        self.consumer_thread.start()
        logger.info("Started RabbitMQ consumer thread")
    
    def stop_consuming(self):
        """Stop consuming messages"""
        self.consuming = False
        if self.consumer_thread and self.consumer_thread.is_alive():
            self.consumer_thread.join()
        logger.info("Stopped consuming crawler events")

# Global event manager instance
event_manager = RabbitMQEventManager()

# Convenience functions
def publish_crawler_event(event_type: CrawlerEvent, data: Dict[str, Any]) -> bool:
    """Publish a crawler event"""
    return event_manager.publish_event(event_type, data)

def register_crawler_event_handler(event_type: CrawlerEvent, handler: Callable):
    """Register an event handler"""
    event_manager.register_event_handler(event_type, handler)

def start_event_system():
    """Start the event system"""
    if event_manager.connect():
        event_manager.start_consuming()
        return True
    return False

def stop_event_system():
    """Stop the event system"""
    event_manager.stop_consuming()
    event_manager.disconnect()