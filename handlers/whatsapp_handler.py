"""
WhatsApp Handler
Manages Whapi API integration for WhatsApp messages
"""

import os
import requests
import base64
from typing import Dict, Any, Optional
from .base_handler import BasePlatformHandler
from utils.logger import get_logger

logger = get_logger(__name__)


class WhatsAppHandler(BasePlatformHandler):
    """
    WhatsApp handler using Whapi API

    Features:
    - Extract messages from webhooks
    - Send messages via Whapi
    - Download media from Whapi
    - Phone number formatting
    """

    def __init__(self, api_token: str, base_url: str = 'https://gate.whapi.cloud'):
        """
        Initialize WhatsApp handler

        Args:
            api_token (str): Whapi API token
            base_url (str): Whapi API base URL
        """
        super().__init__('whatsapp')

        logger.info("="*80)
        logger.info("INITIALIZING WHATSAPP HANDLER (WHAPI)")
        logger.info("="*80)

        self.api_token = api_token
        self.base_url = base_url

        logger.debug(f"API Token: {api_token[:10]}..." if api_token else "Not set")
        logger.debug(f"Base URL: {base_url}")

        logger.info("✓ WhatsApp handler initialized")
        logger.info("="*80)

    def send_message(self, to: str, message: str, **kwargs) -> Dict[str, Any]:
        """
        Send a text message via WhatsApp using Whapi API

        Args:
            to (str): Recipient phone number
            message (str): Message text to send
            **kwargs: Additional parameters (ignored for now)

        Returns:
            dict: {'success': bool, 'error': str or None, 'message_id': str or None}
        """
        logger.info("="*60)
        logger.info("SENDING WHATSAPP MESSAGE")
        logger.info("="*60)

        logger.debug(f"To (raw): {to}")
        logger.debug(f"Message: {message[:100]}..." if len(message) > 100 else f"Message: {message}")

        # Format phone number for WHAPI (must include @s.whatsapp.net suffix)
        formatted_to = self.format_phone_number(to)
        logger.debug(f"To (formatted): {formatted_to}")

        url = f"{self.base_url}/messages/text"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'to': formatted_to,
            'body': message
        }

        try:
            logger.debug(f"Calling Whapi API: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            message_id = response_data.get('id', None)

            logger.info("✓ Message sent successfully")
            logger.info(f"  Message ID: {message_id}")
            logger.info("="*60)

            return {
                'success': True,
                'error': None,
                'message_id': message_id,
                'data': response_data
            }

        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            response_text = http_err.response.text if http_err.response else ''

            if status_code == 401:
                error_msg = "Unauthorized: check WHAPI_API_TOKEN"
            elif status_code == 402:
                error_msg = "Payment required: please check Whapi plan or balance"
            elif status_code == 403:
                error_msg = "Forbidden: check Whapi channel permissions or region"
            elif status_code == 429:
                error_msg = "Too many requests: Whapi rate limit reached, retry later"
            else:
                error_msg = f"HTTP {status_code}: {response_text}" if status_code else str(http_err)

            logger.error("❌ Failed to send WhatsApp message")
            logger.error(f"HTTPError: {error_msg}")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'success': False,
                'error': error_msg,
                'message_id': None
            }

        except Exception as e:
            logger.error("❌ Failed to send WhatsApp message")
            logger.error(f"Error: {str(e)}")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'success': False,
                'error': str(e),
                'message_id': None
            }

    def receive_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Extract message details from Whapi webhook payload

        Args:
            webhook_data (dict): Webhook payload from Whapi

        Returns:
            dict or None: Standardized message dict
        """
        logger.info("="*60)
        logger.info("EXTRACTING MESSAGE FROM WEBHOOK")
        logger.info("="*60)

        logger.debug(f"Webhook keys: {list(webhook_data.keys())}")

        try:
            messages = webhook_data.get('messages', [])
            logger.debug(f"Messages in webhook: {len(messages)}")

            if not messages:
                logger.warning("No messages in webhook")
                return None

            message = messages[0]
            msg_type = message.get('type', 'text')

            logger.debug(f"Message type: {msg_type}")
            logger.debug(f"Message ID: {message.get('id', 'unknown')}")
            logger.debug(f"Full message keys: {list(message.keys())}")
            logger.debug(f"Full message data: {message}")

            # ⚠️ CRITICAL FIX: Skip messages sent BY the bot (outgoing messages)
            # Whapi sends webhooks for BOTH incoming AND outgoing messages
            # from_me: true = Message sent by bot (skip this!)
            # from_me: false = Message from customer (process this)
            from_me = message.get('from_me', False)  # Note: Whapi uses 'from_me', not 'fromMe'
            sender_phone = message.get('from', '')

            logger.info(f"🔍 MESSAGE FILTER: from={sender_phone}, from_me={from_me}")

            if from_me:
                logger.info("⏭️ FILTERING: from_me=True (bot's own message) - SKIPPED")
                return None

            # BACKUP FILTER: Also check if sender is the bot's own phone number
            # This provides additional safety in case fromMe field is not reliable

            # Normalize phone number for comparison (remove @s.whatsapp.net suffix if present)
            sender_phone_clean = sender_phone.replace('@s.whatsapp.net', '')

            # Load bot's phone number from config
            try:
                from core.config_loader import get_config
                config = get_config()
                bot_phone = config.get('platforms.whatsapp.bot_phone', '')

                if bot_phone and sender_phone_clean == bot_phone:
                    logger.warning("⏭️ BACKUP FILTER: Blocking message from bot's own phone number")
                    logger.warning(f"   Sender: {sender_phone_clean} matches bot phone: {bot_phone}")
                    logger.warning("   This prevents bot from responding to its own messages")
                    return None
            except Exception as e:
                logger.debug(f"Could not load bot phone config for backup filter: {e}")
                # Continue with message processing if config not available

            # Message passed all filters - extract and return the message data
            # WHAPI format: message['text'] = {'body': 'actual message text'}
            text_data = message.get('text', {})
            if isinstance(text_data, dict):
                message_text = text_data.get('body', '')
            else:
                message_text = str(text_data) if text_data else ''

            logger.info(f"✅ MESSAGE ACCEPTED: Processing message from {sender_phone}")
            logger.debug(f"   Message text: {message_text[:100]}..." if message_text else "   Message text: EMPTY")

            return {
                'from': sender_phone,
                'message': message_text,
                'type': msg_type,
                'message_id': message.get('id', ''),
                'timestamp': message.get('timestamp', ''),
                'image': message.get('image') if msg_type == 'image' else None,
                'voice': message.get('voice') if msg_type in ['voice', 'audio', 'ptt'] else None,
                'document': message.get('document') if msg_type == 'document' else None,
                'raw_message': message
            }

        except Exception as e:
            logger.error(f"Error extracting message from webhook: {str(e)}")
            logger.exception("Full error traceback:")
            return None

    def send_image(self, to: str, image_url: str, caption: str = "") -> Dict[str, Any]:
        """
        Send an image via WhatsApp using Whapi API

        The image will display inline in WhatsApp (not as a clickable link)

        Args:
            to (str): Recipient phone number
            image_url (str): URL of the image to send
            caption (str, optional): Caption text to display with image

        Returns:
            dict: {'success': bool, 'error': str or None, 'message_id': str or None}
        """
        logger.info("="*60)
        logger.info("SENDING WHATSAPP IMAGE")
        logger.info("="*60)

        logger.debug(f"To (raw): {to}")
        logger.debug(f"Image URL: {image_url}")
        logger.debug(f"Caption: {caption[:100]}..." if caption else "No caption")

        # Format phone number for WHAPI (must include @s.whatsapp.net suffix)
        formatted_to = self.format_phone_number(to)
        logger.debug(f"To (formatted): {formatted_to}")

        url = f"{self.base_url}/messages/image"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        payload = {
            'to': formatted_to,
            'media': image_url
        }

        if caption:
            payload['caption'] = caption

        try:
            logger.debug(f"Calling Whapi API: {url}")
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()

            response_data = response.json()
            message_id = response_data.get('id', None)

            logger.info("✓ Image sent successfully")
            logger.info(f"  Message ID: {message_id}")
            logger.info("="*60)

            return {
                'success': True,
                'error': None,
                'message_id': message_id,
                'data': response_data
            }

        except requests.exceptions.HTTPError as http_err:
            status_code = http_err.response.status_code if http_err.response else None
            response_text = http_err.response.text if http_err.response else ''

            if status_code == 401:
                error_msg = "Unauthorized: check WHAPI_API_TOKEN"
            elif status_code == 402:
                error_msg = "Payment required: please check Whapi plan or balance"
            elif status_code == 403:
                error_msg = "Forbidden: check Whapi channel permissions or region"
            elif status_code == 429:
                error_msg = "Too many requests: Whapi rate limit reached, retry later"
            else:
                error_msg = f"HTTP {status_code}: {response_text}" if status_code else str(http_err)

            logger.error("❌ Failed to send WhatsApp image")
            logger.error(f"HTTPError: {error_msg}")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'success': False,
                'error': error_msg,
                'message_id': None
            }

        except Exception as e:
            logger.error("❌ Failed to send WhatsApp image")
            logger.error(f"Error: {str(e)}")
            logger.exception("Full error traceback:")
            logger.error("="*60)

            return {
                'success': False,
                'error': str(e),
                'message_id': None
            }
    def get_contact_info(self, phone: str) -> Optional[Dict[str, Any]]:
        """
        Fetch WhatsApp contact/profile information from Whapi

        Args:
            phone (str): Phone number to look up (e.g., "60123456789" or "+60123456789")

        Returns:
            dict or None: Contact information with 'name', 'pushName', etc.
        """
        logger.info("="*60)
        logger.info("FETCHING WHATSAPP CONTACT INFO")
        logger.info("="*60)

        # Normalize phone number (remove + and @ suffix)
        normalized_phone = phone.replace('+', '').replace('@s.whatsapp.net', '').replace('-', '').replace(' ', '')

        logger.debug(f"Original phone: {phone}")
        logger.debug(f"Normalized phone: {normalized_phone}")

        url = f"{self.base_url}/contacts/{normalized_phone}"

        headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }

        try:
            logger.debug(f"Calling Whapi API: {url}")
            response = requests.get(url, headers=headers, timeout=10)

            # Handle 404 (contact not found)
            if response.status_code == 404:
                logger.warning(f"⚠️ Contact not found in WhatsApp: {normalized_phone}")
                logger.warning("   This number may not have WhatsApp or is invalid")
                return None

            response.raise_for_status()

            contact_data = response.json()

            logger.info("✓ Contact info retrieved successfully")
            logger.info(f"  Name: {contact_data.get('name', 'N/A')}")
            logger.info(f"  Push Name: {contact_data.get('pushName', 'N/A')}")
            logger.info("="*60)

            return contact_data

        except requests.exceptions.HTTPError as e:
            logger.error(f"❌ HTTP error fetching contact: {e}")
            logger.error(f"   Status code: {response.status_code if response else 'N/A'}")
            return None
        except requests.exceptions.Timeout:
            logger.error("❌ Timeout fetching contact info")
            return None
        except Exception as e:
            logger.error(f"❌ Failed to fetch contact info: {str(e)}")
            logger.exception("Full error traceback:")
            return None

    def process_media(self, media_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Download media from Whapi

        Args:
            media_data (dict): Media information with 'url' or 'link' key

        Returns:
            dict or None: Processed media information
        """
        logger.info(f"Processing media from Whapi")
        logger.debug(f"Media data: {media_data}")

        # Whapi may provide media either as 'url' or 'link'
        url = media_data.get('url') or media_data.get('link')
        if not url:
            logger.error("No URL/link in media data")
            return None

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            logger.debug(f"Downloading from: {url[:50]}...")
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            logger.info(f"✓ Media downloaded ({len(response.content)} bytes)")

            return {
                'type': media_data.get('type', 'unknown'),
                'content': response.content,
                'mime_type': media_data.get('mime_type', 'application/octet-stream'),
                'size': len(response.content)
            }

        except Exception as e:
            logger.error(f"❌ Failed to download media: {str(e)}")
            logger.exception("Full error traceback:")
            return None

    def download_image(self, image_url: str) -> Optional[str]:
        """
        Download image from Whapi and convert to base64

        Args:
            image_url (str): URL to the image from Whapi

        Returns:
            str or None: Base64 encoded image data
        """
        logger.info(f"Downloading image from Whapi")
        logger.debug(f"URL: {image_url[:50]}...")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            response = requests.get(image_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Convert to base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')

            logger.info(f"✓ Image downloaded and encoded ({len(image_base64)} chars)")
            return image_base64

        except Exception as e:
            logger.error(f"❌ Failed to download image: {str(e)}")
            logger.exception("Full error traceback:")
            return None

    def download_audio(self, audio_url: str, save_path: str) -> bool:
        """
        Download audio file from Whapi and save to disk

        Args:
            audio_url (str): URL to the audio file from Whapi
            save_path (str): Path where to save the audio file

        Returns:
            bool: True if successful, False otherwise
        """
        logger.info(f"Downloading audio from Whapi")
        logger.debug(f"URL: {audio_url[:50]}...")
        logger.debug(f"Save path: {save_path}")

        try:
            headers = {
                'Authorization': f'Bearer {self.api_token}'
            }

            response = requests.get(audio_url, headers=headers, timeout=30)
            response.raise_for_status()

            # Save audio file to disk
            with open(save_path, 'wb') as audio_file:
                audio_file.write(response.content)

            file_size_mb = len(response.content) / (1024 * 1024)

            logger.info(f"✓ Audio downloaded and saved ({file_size_mb:.2f} MB)")
            return True

        except Exception as e:
            logger.error(f"❌ Failed to download audio: {str(e)}")
            logger.exception("Full error traceback:")
            return False

    @staticmethod
    def format_phone_number(number: str) -> str:
        """
        Ensure phone number is in correct format for Whapi

        Args:
            number (str): Phone number (can be string or int)

        Returns:
            str: Formatted number (e.g., "60123456789@s.whatsapp.net")
        """
        # Convert to string if it's an integer
        number = str(number)
        logger.debug(f"Formatting phone number: {number}")

        # Remove any non-digit characters
        clean_number = ''.join(filter(str.isdigit, number))

        # Add @s.whatsapp.net if not present
        if '@s.whatsapp.net' not in number:
            formatted = f"{clean_number}@s.whatsapp.net"
        else:
            formatted = number

        logger.debug(f"Formatted number: {formatted}")
        return formatted
