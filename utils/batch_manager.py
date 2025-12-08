"""
Batch Manager for Follow-up Updates
Accumulates message updates and flushes them in batches to Google Sheets
Reduces API calls by consolidating multiple updates into single batch writes
"""
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class BatchUpdate:
    """Represents a single message update to be batched"""

    def __init__(self, phone: str, campaign_id: str, message_num: int,
                 message_text: str, status: str = 'Sent', error: Optional[str] = None):
        """
        Create a batch update entry

        Args:
            phone: Customer's phone number
            campaign_id: Campaign ID
            message_num: Message number sent (1, 2, or 3)
            message_text: The message text that was sent
            status: 'Sent' or 'Failed'
            error: Error message if status is 'Failed'
        """
        self.phone = phone
        self.campaign_id = campaign_id
        self.message_num = message_num
        self.message_text = message_text
        self.status = status
        self.error = error
        self.sent_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for easy JSON serialization"""
        return {
            'phone': self.phone,
            'campaign_id': self.campaign_id,
            'message_num': self.message_num,
            'message_text': self.message_text,
            'status': self.status,
            'error': self.error,
            'sent_time': self.sent_time
        }


class FollowupBatchManager:
    """
    Thread-safe batch manager for follow-up message updates

    Purpose:
    - Accumulate message updates in memory (not Google Sheets)
    - Periodically flush to sheets in bulk operations
    - Reduce API quota usage through batching

    Operation:
    - Throttle send job adds updates to batch (0 API calls)
    - Batch flush job (every 30 min) writes all updates to sheets (3 API calls)
    - Deferred status job (every 30 min) marks messages as 'Queued' in sheets (1 API call)

    Example Flow:
    13:00 - Check job finds 10 messages ready → Adds to in-memory queue
    13:00-13:30 - Send job: pulls 1/3sec, sends WhatsApp, adds to batch
    13:30 - Flush job: writes all 10 to queue sheet (1 API) + logs (1 API)
    14:00 - Next flush job writes another batch
    """

    def __init__(self):
        """Initialize the batch manager"""
        self.pending_updates: List[BatchUpdate] = []
        self.lock = threading.Lock()
        self.flush_count = 0
        self.total_updates_flushed = 0

        logger.info("✅ Followup Batch Manager initialized")

    def add_update(self, phone: str, campaign_id: str, message_num: int,
                   message_text: str, status: str = 'Sent', error: Optional[str] = None) -> bool:
        """
        Add a message update to the batch

        Called by throttle send job after WhatsApp message is sent

        Args:
            phone: Customer's phone number
            campaign_id: Campaign ID
            message_num: Message number (1, 2, or 3)
            message_text: The message text
            status: 'Sent' or 'Failed'
            error: Error message if failed

        Returns:
            True if added successfully
        """
        try:
            with self.lock:
                update = BatchUpdate(phone, campaign_id, message_num, message_text, status, error)
                self.pending_updates.append(update)

                logger.debug(f"📌 Batch add: {phone} (msg {message_num}). Pending: {len(self.pending_updates)}")
                return True

        except Exception as e:
            logger.error(f"❌ Error adding batch update: {e}")
            return False

    def get_pending(self) -> List[BatchUpdate]:
        """
        Get all pending updates and clear the batch

        Called by flush job before writing to sheets

        Returns:
            List of BatchUpdate objects
        """
        try:
            with self.lock:
                updates = self.pending_updates.copy()
                count = len(updates)
                self.pending_updates.clear()

                if count > 0:
                    logger.info(f"📦 Batch retrieved: {count} updates ready to flush")

                return updates

        except Exception as e:
            logger.error(f"❌ Error getting pending updates: {e}")
            return []

    def mark_flushed(self, count: int) -> None:
        """
        Record that a batch flush was completed

        Args:
            count: Number of updates that were flushed
        """
        try:
            with self.lock:
                self.flush_count += 1
                self.total_updates_flushed += count
                logger.info(f"✅ Batch flush #{self.flush_count}: {count} updates → Google Sheets")

        except Exception as e:
            logger.error(f"❌ Error marking flush: {e}")

    def size(self) -> int:
        """Get current number of pending updates"""
        with self.lock:
            return len(self.pending_updates)

    def has_pending(self) -> bool:
        """Check if there are any pending updates"""
        with self.lock:
            return len(self.pending_updates) > 0

    def clear(self) -> int:
        """
        Clear all pending updates (emergency only)

        Returns:
            Number of updates cleared
        """
        try:
            with self.lock:
                count = len(self.pending_updates)
                self.pending_updates.clear()
                logger.warning(f"⚠️  Batch cleared: {count} updates removed")
                return count
        except Exception as e:
            logger.error(f"❌ Error clearing batch: {e}")
            return 0

    def get_stats(self) -> Dict[str, Any]:
        """
        Get batch manager statistics

        Returns:
            Dictionary with batch metrics
        """
        try:
            with self.lock:
                return {
                    'pending_updates': len(self.pending_updates),
                    'total_flushes': self.flush_count,
                    'total_updates_flushed': self.total_updates_flushed,
                    'average_batch_size': self.total_updates_flushed / max(self.flush_count, 1)
                }
        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {
                'pending_updates': 0,
                'total_flushes': 0,
                'total_updates_flushed': 0,
                'average_batch_size': 0
            }


# Global batch manager instance
followup_batch_manager = FollowupBatchManager()
