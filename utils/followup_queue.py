"""
Follow-up Message Queue
Manages in-memory queue for follow-up messages ready to send
Provides thread-safe operations for minimal API quota usage
"""
from collections import deque
import threading
from typing import Optional, Dict, Any
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class FollowupMessageQueue:
    """
    Thread-safe in-memory queue for follow-up messages

    Purpose:
    - Store messages ready to send in RAM (not Google Sheets)
    - Allow throttled send job to pull 1 message per 3 seconds
    - Reduce API calls by batching sheet reads/writes

    Key Benefits:
    - 0 API calls for queue operations (everything in RAM)
    - Thread-safe with locks
    - Tracks metrics (queue size, messages processed)
    """

    def __init__(self):
        """Initialize the message queue"""
        self.queue = deque()  # FIFO queue of messages ready to send
        self.lock = threading.Lock()  # Thread safety for concurrent access
        self.processed_count = 0  # Total messages processed
        self.start_time = datetime.now()

        logger.info("✅ Followup Message Queue initialized")

    def add_message(self, phone: str, campaign_id: str, message_num: int) -> bool:
        """
        Add a message to the queue (from check job)

        Args:
            phone: Customer's phone number
            campaign_id: Campaign ID
            message_num: Message number (1, 2, or 3)

        Returns:
            True if added successfully
        """
        try:
            with self.lock:
                message = {
                    'phone': phone,
                    'campaign_id': campaign_id,
                    'message_num': message_num,
                    'queued_at': datetime.now().isoformat()
                }
                self.queue.append(message)

                logger.debug(f"📝 Added to queue: {phone} (Campaign {campaign_id}, Message {message_num}). Queue size: {len(self.queue)}")
                return True

        except Exception as e:
            logger.error(f"❌ Error adding message to queue: {e}")
            return False

    def get_next(self) -> Optional[Dict[str, Any]]:
        """
        Get next message from queue (from send job)
        Thread-safe FIFO pop

        Returns:
            Message dict or None if queue is empty
        """
        try:
            with self.lock:
                if len(self.queue) > 0:
                    message = self.queue.popleft()
                    self.processed_count += 1
                    logger.debug(f"📤 Pulled from queue: {message['phone']}. Queue size: {len(self.queue)}")
                    return message
                return None

        except Exception as e:
            logger.error(f"❌ Error getting next message: {e}")
            return None

    def size(self) -> int:
        """Get current queue size (messages waiting to send)"""
        with self.lock:
            return len(self.queue)

    def peek(self) -> Optional[Dict[str, Any]]:
        """
        Peek at next message without removing it
        Useful for logging/debugging

        Returns:
            Next message dict or None
        """
        try:
            with self.lock:
                if len(self.queue) > 0:
                    return self.queue[0]
                return None
        except Exception as e:
            logger.error(f"❌ Error peeking queue: {e}")
            return None

    def clear(self) -> int:
        """
        Clear the entire queue (emergency only)

        Returns:
            Number of messages cleared
        """
        try:
            with self.lock:
                count = len(self.queue)
                self.queue.clear()
                logger.warning(f"⚠️  Queue cleared. {count} messages removed")
                return count
        except Exception as e:
            logger.error(f"❌ Error clearing queue: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get queue statistics

        Returns:
            Dictionary with queue metrics
        """
        try:
            with self.lock:
                uptime = (datetime.now() - self.start_time).total_seconds()
                return {
                    'queue_size': len(self.queue),
                    'total_processed': self.processed_count,
                    'uptime_seconds': uptime,
                    'processing_rate': self.processed_count / max(uptime, 1)  # msgs/sec
                }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {
                'queue_size': 0,
                'total_processed': 0,
                'uptime_seconds': 0,
                'processing_rate': 0
            }


# Global queue instance (created once per app instance)
followup_message_queue = FollowupMessageQueue()
