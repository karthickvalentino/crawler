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
        
        # Connections and channels
        self.publisher_connection = None
        self.consumer_connection = None
        self.consumer_channel = None
        self.consuming = False
        self.consumer_thread = None
        
        # Event handlers
        self.event_handlers: Dict[str, Callable] = {}
        
        # Queue and exchange names
        self.crawler_exchange = 'crawler_events'
        self.crawler_queue = 'crawler_commands'
        self.status_queue = 'crawler_status'

        self.publisher_thread_local = threading.local()
        
        logger.info(f"Initialized RabbitMQ Event Manager for {self.host}:{self.port}")
    
    def _create_connection(self) -> Optional[pika.BlockingConnection]:
        """Create a new connection to RabbitMQ"""
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
            return pika.BlockingConnection(parameters)
        except Exception as e:
            logger.error(f"Failed to create RabbitMQ connection: {str(e)}")
            return None

    def _get_publisher_channel(self) -> Optional[pika.channel.Channel]:
        """Get a channel for the current thread."""
        if not hasattr(self.publisher_thread_local, "connection") or self.publisher_thread_local.connection.is_closed:
            self.publisher_thread_local.connection = self._create_connection()
            if self.publisher_thread_local.connection is None:
                return None
        
        if not hasattr(self.publisher_thread_local, "channel") or self.publisher_thread_local.channel.is_closed:
            self.publisher_thread_local.channel = self.publisher_thread_local.connection.channel()
            self.publisher_thread_local.channel.exchange_declare(
                exchange=self.crawler_exchange,
                exchange_type='topic',
                durable=True
            )
        return self.publisher_thread_local.channel

    def connect_consumer(self) -> bool:
        """Establish consumer connection to RabbitMQ"""
        if self.consumer_connection and self.consumer_connection.is_open:
            return True
        
        self.consumer_connection = self._create_connection()
        if not self.consumer_connection:
            return False
            
        self.consumer_channel = self.consumer_connection.channel()
        
        # Declare exchange
        self.consumer_channel.exchange_declare(
            exchange=self.crawler_exchange,
            exchange_type='topic',
            durable=True
        )
        
        # Declare queues
        self.consumer_channel.queue_declare(queue=self.crawler_queue, durable=True)
        self.consumer_channel.queue_declare(queue=self.status_queue, durable=True)
        
        # Bind queues
        self.consumer_channel.queue_bind(
            exchange=self.crawler_exchange,
            queue=self.crawler_queue,
            routing_key='crawler.command.*'
        )
        self.consumer_channel.queue_bind(
            exchange=self.crawler_exchange,
            queue=self.status_queue,
            routing_key='crawler.status.*'
        )
        
        logger.info("Consumer connected to RabbitMQ successfully")
        return True
    
    def disconnect(self):
        """Close all RabbitMQ connections"""
        self.stop_consuming()
        
        # Close publisher connections for the current thread
        if hasattr(self.publisher_thread_local, "connection") and self.publisher_thread_local.connection.is_open:
            self.publisher_thread_local.connection.close()
            logger.info("Disconnected publisher from RabbitMQ for current thread")

        # Close consumer connection
        try:
            if self.consumer_connection and self.consumer_connection.is_open:
                self.consumer_connection.close()
                logger.info("Disconnected consumer from RabbitMQ")
        except Exception as e:
            logger.error(f"Error disconnecting consumer from RabbitMQ: {str(e)}")
    
    def publish_event(self, event_type: CrawlerEvent, data: Dict[str, Any], routing_key: str = None) -> bool:
        try:
            channel = self._get_publisher_channel()
            if not channel:
                logger.error("Could not get a publisher channel.")
                return False

            message = {
                'event_type': event_type.value,
                'timestamp': datetime.now().isoformat(),
                'data': data
            }

            if not routing_key:
                routing_key = f'crawler.command.{event_type.value}'

            channel.basic_publish(
                exchange=self.crawler_exchange,
                routing_key=routing_key,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2, # make message persistent
                    timestamp=int(time.time())
                )
            )
            logger.info(f"Published {event_type.value} to {routing_key}")
            return True

        except pika.exceptions.AMQPConnectionError as e:
            logger.error(f"AMQP connection failed during publish: {e}")
            # Connection will be re-established on next call
            if hasattr(self.publisher_thread_local, "connection"):
                self.publisher_thread_local.connection.close()
            return False
        except Exception as e:
            logger.exception(f"Failed to publish event: {e}")
            return False
    
    def register_event_handler(self, event_type: CrawlerEvent, handler: Callable):
        """Register an event handler for a specific event type"""
        self.event_handlers[event_type.value] = handler
        logger.info(f"Registered handler for event: {event_type.value}")
    
    def _handle_message(self, channel, method, properties, body):
        """Handle incoming RabbitMQ message"""
        try:
            message = json.loads(body.decode('utf-8'))
            event_type = message.get('event_type')
            data = message.get('data', {})
            
            logger.debug(f"Received event: {event_type}")
            
            if event_type in self.event_handlers:
                try:
                    self.event_handlers[event_type](data)
                    channel.basic_ack(delivery_tag=method.delivery_tag)
                    logger.debug(f"Successfully handled event: {event_type}")
                except Exception as e:
                    logger.error(f"Error handling event {event_type}: {str(e)}")
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            else:
                logger.warning(f"No handler registered for event: {event_type}")
                channel.basic_ack(delivery_tag=method.delivery_tag)
                
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    def start_consuming(self):
        """Start consuming events in a separate thread."""
        if self.consuming:
            logger.warning("Consumer is already running.")
            return

        def consume():
            self.consuming = True
            logger.info("Consumer thread started.")
            while self.consuming:
                try:
                    if not self.connect_consumer():
                        logger.error("Consumer could not connect. Retrying in 5 seconds.")
                        time.sleep(5)
                        continue
                    
                    self.consumer_channel.basic_qos(prefetch_count=1)
                    self.consumer_channel.basic_consume(
                        queue=self.crawler_queue,
                        on_message_callback=self._handle_message
                    )
                    logger.info("Started consuming crawler events")
                    self.consumer_channel.start_consuming()
                except (pika.exceptions.ConnectionClosedByBroker, pika.exceptions.AMQPConnectionError) as e:
                    logger.warning(f"Consumer connection lost: {e}. Reconnecting...")
                    time.sleep(5)
                except Exception as e:
                    logger.error(f"Critical error in consumer thread: {str(e)}")
                    self.consuming = False
            logger.info("Consumer thread stopped.")

        self.consumer_thread = threading.Thread(target=consume, daemon=True)
        self.consumer_thread.start()

    def stop_consuming(self):
        """Stop the consumer thread."""
        if not self.consuming:
            return
        
        try:
            self.consuming = False
            if self.consumer_channel and self.consumer_channel.is_open:
                self.consumer_channel.stop_consuming()
            if self.consumer_thread and self.consumer_thread.is_alive():
                self.consumer_thread.join(timeout=5)
            logger.info("Stopped consuming crawler events")
        except Exception as e:
            logger.error(f"Error stopping consumer: {e}")


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
    """Start the event system's consumer"""
    event_manager.start_consuming()
    return True

def stop_event_system():
    """Stop the event system"""
    event_manager.disconnect()
