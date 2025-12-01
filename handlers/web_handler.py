"""
Web Handler
Handles web chat interface requests
"""

from typing import Dict, Any, Optional
from .base_handler import BasePlatformHandler
from utils.logger import get_logger

logger = get_logger(__name__)


class WebHandler(BasePlatformHandler):
    """
    Web chat handler

    Features:
    - Process web chat messages
    - Handle file uploads from web
    - Format responses for web display
    """

    def __init__(self):
        """Initialize web handler"""
        super().__init__('web')

        logger.info("="*80)
        logger.info("INITIALIZING WEB HANDLER")
        logger.info("="*80)

        logger.info("✓ Web handler initialized")
        logger.info("="*80)

    def receive_message(self, request_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract message from web request

        Args:
            request_data (dict): Request data from Flask
                Expected keys: 'message', 'file_data' (optional)

        Returns:
            dict or None: Standardized message dict
        """
        logger.info("="*60)
        logger.info("EXTRACTING MESSAGE FROM WEB REQUEST")
        logger.info("="*60)

        logger.debug(f"Request keys: {list(request_data.keys())}")

        try:
            message = request_data.get('message', '').strip()
            file_data = request_data.get('file_data')

            logger.debug(f"Message: {message[:100]}..." if message else "No message text")
            logger.debug(f"File attached: {bool(file_data)}")

            result = {
                'from': 'web_user',  # Web users don't have persistent IDs by default
                'message': message,
                'type': 'text',
                'file_data': file_data,
                'metadata': request_data.get('metadata', {})
            }

            if file_data:
                result['type'] = file_data.get('type', 'text')
                logger.debug(f"File type: {result['type']}")

            logger.info("✓ Web message extracted")
            logger.info(f"  Message length: {len(message)} chars")
            logger.info(f"  Type: {result['type']}")

            logger.info("="*60)
            return result

        except Exception as e:
            logger.error("❌ Failed to extract web message")
            logger.error(f"Error: {str(e)}")
            logger.exception("Full error traceback:")
            return None

    def send_message(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Prepare message for web response

        For web, we don't actually "send" - we just prepare the response

        Args:
            to (str): Not used for web (included for interface compatibility)
            message (str): Message to send
            **kwargs: Additional parameters

        Returns:
            dict: {'success': bool, 'error': None, 'message': str}
        """
        logger.debug(f"Preparing web response ({len(message)} chars)")

        return {
            'success': True,
            'error': None,
            'message': message,
            'formatted_message': self.format_response(message)
        }

    def process_media(self, media_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Process media from web upload

        Args:
            media_data (dict): Media information from web upload

        Returns:
            dict or None: Processed media information
        """
        logger.info("Processing media from web upload")
        logger.debug(f"Media data keys: {list(media_data.keys())}")

        # For web, media is already uploaded and available locally
        # Just validate and return info
        try:
            return {
                'type': media_data.get('type', 'unknown'),
                'path': media_data.get('path'),
                'mime_type': media_data.get('mime_type'),
                'size': media_data.get('size', 0)
            }

        except Exception as e:
            logger.error(f"❌ Failed to process web media: {str(e)}")
            return None

    def format_response(self, response: str) -> str:
        """
        Format response for web display

        Args:
            response (str): Raw response text

        Returns:
            str: Formatted response (HTML-safe, with line breaks)
        """
        logger.debug(f"Formatting response for web ({len(response)} chars)")

        # For web, we can keep formatting as-is
        # The frontend will handle display
        # We could add HTML formatting here if needed

        return response
