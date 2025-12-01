"""
Base Handler
Abstract base class for all platform handlers
Defines standard interface for platform integration
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class BasePlatformHandler(ABC):
    """
    Abstract base class for platform handlers

    All platform handlers (WhatsApp, Web, Telegram, etc.) should inherit from this class
    and implement the required methods.

    This ensures consistent interface across all platforms.
    """

    def __init__(self, platform_name: str):
        """
        Initialize platform handler

        Args:
            platform_name (str): Name of the platform (e.g., 'whatsapp', 'web', 'telegram')
        """
        self.platform_name = platform_name
        logger.info(f"Initializing {platform_name} handler")

    @abstractmethod
    def receive_message(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract message from platform-specific request data

        Args:
            request_data (dict): Raw request data from platform

        Returns:
            dict or None: Standardized message dict with keys:
                - 'from': sender identifier
                - 'message': message text
                - 'type': message type ('text', 'image', 'voice', etc.)
                - 'media': media data if applicable
                - 'metadata': additional platform-specific data
        """
        pass

    @abstractmethod
    def send_message(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send message via platform

        Args:
            to (str): Recipient identifier
            message (str): Message text to send
            **kwargs: Additional platform-specific parameters

        Returns:
            dict: Result with keys:
                - 'success': bool
                - 'error': str or None
                - 'message_id': str or None
        """
        pass

    @abstractmethod
    def process_media(self, media_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process media from message (download, convert, etc.)

        Args:
            media_data (dict): Media information from message

        Returns:
            dict or None: Processed media with keys:
                - 'type': media type ('image', 'voice', 'document')
                - 'path': local file path
                - 'mime_type': MIME type
                - 'size': file size in bytes
        """
        pass

    def format_response(self, response: str) -> str:
        """
        Format response for platform-specific requirements

        Default implementation returns response as-is.
        Override in subclass for platform-specific formatting.

        Args:
            response (str): Raw response text

        Returns:
            str: Formatted response
        """
        logger.debug(f"Formatting response for {self.platform_name} ({len(response)} chars)")
        return response

    def log_activity(self, activity: str, details: Optional[Dict[str, Any]] = None):
        """
        Log platform activity

        Args:
            activity (str): Activity description
            details (dict, optional): Additional details
        """
        logger.info(f"[{self.platform_name.upper()}] {activity}")
        if details:
            logger.debug(f"Details: {details}")
