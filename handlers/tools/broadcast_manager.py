"""
Broadcast Manager Tool
Manages scheduled promotional message broadcasts
Staff can add scheduled messages in Google Sheets and system auto-sends at scheduled time

Supports:
- Text messages
- Image messages with caption (format: image_url|caption_text)
- Retry until success with exponential backoff
"""
import gspread
import time
import re
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple, Callable
import json
from utils.logger import get_logger
from utils.rate_limiter import throttle_if_busy, track_api_call
from utils.cache_manager import CacheManager

logger = get_logger(__name__)

def download_google_drive_image(url_or_id: str):
    """Download image from Google Drive and return as base64 data URI"""
    try:
        import requests as req
        import base64 as b64
        
        # Extract file ID
        file_id = None
        gdrive_match = re.search(r'drive\.google\.com/file/d/([^/]+)', url_or_id)
        if gdrive_match:
            file_id = gdrive_match.group(1)
        elif re.match(r'^[a-zA-Z0-9_-]{20,}$', url_or_id.strip()):
            file_id = url_or_id.strip()
        
        if not file_id:
            return (None, 'Could not extract Google Drive file ID')
        
        download_url = f'https://drive.google.com/uc?export=download&id={file_id}&confirm=t'
        response = req.get(download_url, timeout=60)
        
        if response.status_code != 200:
            return (None, f'Download failed with status {response.status_code}')
        
        content = response.content
        
        # Detect image type from magic bytes
        jpeg_sig = bytes([0xff, 0xd8, 0xff])
        png_sig = bytes([0x89, 0x50, 0x4e, 0x47])
        
        if content[:3] == jpeg_sig:
            mime_type = 'image/jpeg'
        elif content[:4] == png_sig:
            mime_type = 'image/png'
        elif content[:6] == b'GIF87a' or content[:6] == b'GIF89a':
            mime_type = 'image/gif'
        else:
            # Check if HTML
            if b'<!doctype' in content[:100].lower() or b'<html' in content[:100].lower():
                return (None, 'Google Drive returned HTML - file may not be publicly accessible')
            mime_type = 'image/jpeg'
        
        image_base64 = b64.b64encode(content).decode('utf-8')
        data_uri = f'data:{mime_type};base64,{image_base64}'
        
        logger.info(f'   Downloaded Google Drive image: {len(content)} bytes, {mime_type}')
        return (data_uri, None)
        
    except Exception as e:
        return (None, f'Download error: {str(e)}')



import requests
import base64


def is_google_drive_url(url: str) -> bool:
    """Check if URL is a Google Drive URL or file ID"""
    if not url:
        return False
    url = url.strip()
    
    if 'drive.google.com' in url:
        return True
    
    # Check if it looks like a file ID (20+ alphanumeric chars)
    if re.match(r'^[a-zA-Z0-9_-]{20,}$', url) and '.' not in url and '/' not in url:
        return True
    
    return False


# Image URL extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')

# Retry configuration
MAX_RETRY_ATTEMPTS = 10
INITIAL_RETRY_DELAY = 2  # seconds
MAX_RETRY_DELAY = 60  # seconds
BROADCAST_DELAY_SECONDS = 60  # Delay between each message to avoid spam detection


class BroadcastManager:
    """
    Manages scheduled broadcast messages for promotional campaigns
    Integrates with Google Sheets for broadcast management and tracking

    Features:
    - Staff adds recipients to "Broadcast Recipients" sheet
    - Staff schedules messages in "Scheduled Broadcasts" sheet
    - System auto-sends at scheduled time
    - Logs all deliveries in "Broadcast Logs" sheet
    - Supports text and image messages
    - Retry until success with exponential backoff
    """

    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """
        Initialize Broadcast Manager with Google Sheets connection

        Args:
            credentials_file: Path to Google service account JSON
            spreadsheet_name: Name/ID of Google Sheet to use
        """
        logger.info("Initializing Broadcast Manager...")

        # Define Google Sheets API scope
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]

        try:
            # Authenticate using service account
            logger.info(f"Loading credentials from: {credentials_file}")
            credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=SCOPES
            )

            # Connect to Google Sheets
            self.gc = gspread.authorize(credentials)

            # Open spreadsheet
            logger.info(f"Opening spreadsheet: {spreadsheet_name}")
            try:
                self.spreadsheet = self.gc.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                if 'docs.google.com/spreadsheets/d/' in spreadsheet_name:
                    self.spreadsheet = self.gc.open_by_url(spreadsheet_name)
                else:
                    self.spreadsheet = self.gc.open_by_key(spreadsheet_name)

            # Initialize sheets (create if don't exist)
            self._init_sheets()

            logger.info("Broadcast Manager initialized successfully!")
            logger.info(f"   Spreadsheet: {spreadsheet_name}")
            logger.info(f"   Recipients Sheet: {self.recipients_sheet.title}")
            logger.info(f"   Broadcasts Sheet: {self.broadcasts_sheet.title}")
            logger.info(f"   Logs Sheet: {self.logs_sheet.title}")

        except FileNotFoundError:
            logger.error(f"Credentials file not found: {credentials_file}")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Broadcast Manager: {e}")
            raise

    def _init_sheets(self):
        """Initialize all required sheets, create if they don't exist"""

        # Define sheet configurations
        sheets_config = {
            "Broadcast Recipients": [
                "Name", "Phone", "Status", "Added Date", "Notes"
            ],
            "Scheduled Broadcasts": [
                "Broadcast ID", "Title", "Message", "Schedule Date",
                "Schedule Time", "Target List", "Status", "Sent Count",
                "Created Date", "Sent Date"
            ],
            "Broadcast Logs": [
                "Broadcast ID", "Title", "Phone", "Name", "Sent Time",
                "Delivery Status", "Message Type", "Retry Count", "Response Text"
            ]
        }

        # Access or create each sheet
        for sheet_name, headers in sheets_config.items():
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                logger.info(f"   Found sheet: {sheet_name}")
            except gspread.WorksheetNotFound:
                logger.info(f"   Sheet not found: {sheet_name}, creating...")
                worksheet = self.spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )
                worksheet.update('A1', [headers])
                worksheet.format('A1:Z1', {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.2, "green": 0.6, "blue": 0.9}
                })
                worksheet.freeze(rows=1)
                logger.info(f"   Created sheet: {sheet_name}")

        # Store sheet references
        self.recipients_sheet = self.spreadsheet.worksheet("Broadcast Recipients")
        self.broadcasts_sheet = self.spreadsheet.worksheet("Scheduled Broadcasts")
        self.logs_sheet = self.spreadsheet.worksheet("Broadcast Logs")

        # Column mappings for easier access
        self.recipient_cols = {
            'name': 0, 'phone': 1, 'status': 2, 'added_date': 3, 'notes': 4
        }

        self.broadcast_cols = {
            'id': 0, 'title': 1, 'message': 2, 'schedule_date': 3,
            'schedule_time': 4, 'target_list': 5, 'status': 6,
            'sent_count': 7, 'created_date': 8, 'sent_date': 9
        }

        self.log_cols = {
            'broadcast_id': 0, 'title': 1, 'phone': 2, 'name': 3,
            'sent_time': 4, 'delivery_status': 5, 'message_type': 6,
            'retry_count': 7, 'response_text': 8
        }


    @staticmethod
    def _convert_to_direct_image_url(url: str) -> str:
        """
        Convert sharing URLs to direct image URLs
        
        Supports:
        - Google Drive: /file/d/ID/view -> /uc?export=view&id=ID
        - Already direct URLs are returned as-is
        
        Args:
            url: Original URL (may be sharing link or direct)
            
        Returns:
            Direct image URL
        """
        if not url:
            return url
            
        url = url.strip()
        
        # Google Drive conversion
        # Format: https://drive.google.com/file/d/FILE_ID/view?usp=...
        gdrive_match = re.search(r'drive\.google\.com/file/d/([^/]+)', url)
        if gdrive_match:
            file_id = gdrive_match.group(1)
            # Use lh3.googleusercontent.com format - works better with WhatsApp
            return f'https://drive.google.com/uc?export=view&id={file_id}'
        
        # Already a direct Google Drive URL
        if 'drive.google.com/uc?' in url or 'lh3.googleusercontent.com' in url:
            return url
            
        # Return original URL for other cases
        return url

    @staticmethod
    def _is_image_url(text: str) -> bool:
        """
        Check if text is an image URL

        Args:
            text: Text to check

        Returns:
            True if text is an image URL
        """
        if not text:
            return False

        text = text.strip().lower()

        # Check if starts with http/https
        if not (text.startswith('http://') or text.startswith('https://')):
            return False

        # Check for image extensions
        # Remove query parameters for extension check
        url_without_params = text.split('?')[0]

        if url_without_params.endswith(IMAGE_EXTENSIONS):
            return True

        # Also check for common image hosting patterns
        image_hosts = ['imgur.com', 'i.imgur.com', 'images.', 'img.', 'cdn.', 'drive.google.com', 'gstatic.com', 'googleusercontent.com', 'fbcdn.net', 'twimg.com']
        for host in image_hosts:
            if host in text:
                return True

        return False

    @staticmethod
    def _parse_message_content(message: str) -> Dict[str, Any]:
        """
        Parse message content to determine type and extract components

        Format for image with caption: image_url|caption_text
        Format for text only: just the text
        Format for image only: just the image_url
        
        For Google Drive URLs/IDs: Downloads and converts to base64 data URI

        Args:
            message: Raw message from spreadsheet

        Returns:
            Dict with keys: 'type' ('text' or 'image'), 'content', 'caption'
        """
        if not message:
            return {'type': 'text', 'content': '', 'caption': ''}

        message = message.strip()
        image_content = None
        caption = ''

        # Check for pipe separator
        if '|' in message:
            parts = message.split('|', 1)
            first_part = parts[0].strip()
            caption = parts[1].strip() if len(parts) > 1 else ''

            # Check if first part is image URL or Google Drive ID
            if BroadcastManager._is_image_url(first_part) or is_google_drive_url(first_part):
                image_content = first_part
            else:
                return {'type': 'text', 'content': message, 'caption': ''}
        else:
            # No pipe - check if entire message is image
            if BroadcastManager._is_image_url(message) or is_google_drive_url(message):
                image_content = message
            else:
                return {'type': 'text', 'content': message, 'caption': ''}

        # Process image content
        if image_content:
            # Check if it's a Google Drive URL/ID - need to download and convert to base64
            if is_google_drive_url(image_content):
                logger.info(f'   Detected Google Drive URL/ID, downloading...')
                data_uri, error = download_google_drive_image(image_content)
                if data_uri:
                    return {'type': 'image', 'content': data_uri, 'caption': caption}
                else:
                    logger.error(f'   Failed to download Google Drive image: {error}')
                    # Fall back to text message with URL
                    return {"type": "text", "content": image_content + " " + caption, "caption": ""}
            else:
                # Regular image URL
                return {
                    'type': 'image',
                    'content': BroadcastManager._convert_to_direct_image_url(image_content),
                    'caption': caption
                }

        return {'type': 'text', 'content': message, 'caption': ''}

    def _send_with_retry(
        self,
        phone: str,
        parsed_message: Dict[str, Any],
        send_text_func: Callable,
        send_image_func: Callable
    ) -> Tuple[bool, int]:
        """
        Send message with retry until success

        Args:
            phone: Recipient phone number
            parsed_message: Parsed message dict with type, content, caption
            send_text_func: Function to send text (phone, message) -> bool
            send_image_func: Function to send image (phone, image_url, caption) -> bool

        Returns:
            Tuple of (success: bool, retry_count: int)
        """
        msg_type = parsed_message['type']
        content = parsed_message['content']
        caption = parsed_message['caption']

        retry_count = 0
        delay = INITIAL_RETRY_DELAY

        while retry_count < MAX_RETRY_ATTEMPTS:
            try:
                if msg_type == 'image':
                    success = send_image_func(phone, content, caption)
                else:
                    success = send_text_func(phone, content)

                if success:
                    return (True, retry_count)

                # If not successful, retry
                retry_count += 1
                if retry_count < MAX_RETRY_ATTEMPTS:
                    logger.warning(f"      Attempt {retry_count} failed, retrying in {delay}s...")
                    time.sleep(delay)
                    # Exponential backoff with cap
                    delay = min(delay * 2, MAX_RETRY_DELAY)

            except Exception as e:
                retry_count += 1
                logger.error(f"      Attempt {retry_count} error: {e}")
                if retry_count < MAX_RETRY_ATTEMPTS:
                    logger.warning(f"      Retrying in {delay}s...")
                    time.sleep(delay)
                    delay = min(delay * 2, MAX_RETRY_DELAY)

        # All retries exhausted
        return (False, retry_count)

    def get_all_recipients(self) -> List[Dict[str, Any]]:
        """
        Get all active recipients from the recipients sheet

        Returns:
            List of recipient dictionaries
        """
        try:
            throttle_if_busy()
            records = self.recipients_sheet.get_all_records()
            track_api_call()
            # Filter only active recipients
            active_recipients = [
                r for r in records
                if str(r.get('Status', '')).lower() == 'active' and r.get('Phone')
            ]
            logger.info(f"Found {len(active_recipients)} active recipients")
            return active_recipients
        except Exception as e:
            logger.error(f"Error fetching recipients: {e}")
            return []

    def get_pending_broadcasts(self) -> List[Dict[str, Any]]:
        """
        Get all broadcasts that are ready to be sent

        Checks:
        - Status is "Pending"
        - Current date/time >= scheduled date/time

        Returns:
            List of broadcast dictionaries ready to send
        """
        try:
            throttle_if_busy()
            records = self.broadcasts_sheet.get_all_records()
            track_api_call()
            now = datetime.now()

            pending = []
            for record in records:
                # Only process if status is Pending
                status = str(record.get('Status', '')).strip().lower()
                broadcast_id = record.get('Broadcast ID', 'UNKNOWN')
                logger.debug(f"   Checking broadcast {broadcast_id}: status='{status}'")

                if status != 'pending':
                    continue

                # Check if it's time to send
                schedule_date_str = str(record.get('Schedule Date', '')).strip()
                schedule_time_str = str(record.get('Schedule Time', '')).strip()

                if not schedule_date_str or not schedule_time_str:
                    logger.debug(f"   {broadcast_id} missing date/time")
                    continue

                logger.debug(f"   Parsed date: '{schedule_date_str}', time: '{schedule_time_str}'")

                try:
                    # Parse schedule date and time
                    schedule_datetime = None
                    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            date_obj = datetime.strptime(schedule_date_str, date_format)
                            if len(schedule_time_str.split(':')) == 2:
                                time_format = '%H:%M'
                            else:
                                time_format = '%H:%M:%S'
                            time_obj = datetime.strptime(schedule_time_str, time_format).time()
                            schedule_datetime = datetime.combine(date_obj.date(), time_obj)
                            logger.debug(f"   Successfully parsed datetime: {schedule_datetime}")
                            break
                        except ValueError:
                            continue

                    if not schedule_datetime:
                        logger.debug(f"   {broadcast_id}: Invalid date/time format")
                        continue

                    if schedule_datetime <= now:
                        pending.append(record)
                        logger.debug(f"   {broadcast_id} is ready to send")
                    else:
                        logger.debug(f"   {broadcast_id} not yet ready")

                except Exception as e:
                    logger.warning(f"Error parsing schedule for {record.get('Broadcast ID')}: {e}")
                    continue

            logger.info(f"Found {len(pending)} broadcasts ready to send")
            return pending

        except Exception as e:
            logger.error(f"Error fetching pending broadcasts: {e}")
            return []

    def send_broadcast(
        self,
        broadcast: Dict[str, Any],
        send_function: Callable = None,
        send_text_function: Callable = None,
        send_image_function: Callable = None
    ) -> Dict[str, Any]:
        """
        Send broadcast to all recipients with image support and retry logic

        Args:
            broadcast: Broadcast record from sheet
            send_function: Legacy - Function to send text message (phone, message) -> bool
            send_text_function: Function to send text message (phone, message) -> bool
            send_image_function: Function to send image (phone, image_url, caption) -> bool

        Returns:
            dict with stats: {'sent': int, 'failed': int, 'total': int}
        """
        try:
            broadcast_id = broadcast.get('Broadcast ID', 'UNKNOWN')
            title = broadcast.get('Title', 'Untitled')
            message = broadcast.get('Message', '')

            logger.info("="*80)
            logger.info(f"SENDING BROADCAST: {broadcast_id} - {title}")
            logger.info("="*80)

            if not message:
                logger.error(f"Broadcast {broadcast_id} has no message content")
                return {'sent': 0, 'failed': 0, 'total': 0}

            # Parse message to determine type
            parsed_message = self._parse_message_content(message)
            msg_type = parsed_message['type']

            logger.info(f"Message type: {msg_type.upper()}")
            if msg_type == 'image':
                logger.info(f"   Image URL: {parsed_message['content'][:80]}...")
                if parsed_message['caption']:
                    logger.info(f"   Caption: {parsed_message['caption'][:80]}...")

            # Handle legacy send_function parameter
            if send_function and not send_text_function:
                send_text_function = send_function

            # Validate we have the required send functions
            if msg_type == 'image' and not send_image_function:
                logger.error(f"Image broadcast requested but no send_image_function provided")
                logger.info(f"   Falling back to text-only mode")
                # Fallback: send image URL as text
                msg_type = 'text'
                if parsed_message['caption']:
                    parsed_message['content'] = f"{parsed_message['content']}\n\n{parsed_message['caption']}"
                parsed_message['type'] = 'text'

            if not send_text_function:
                logger.error(f"No send function provided")
                return {'sent': 0, 'failed': 0, 'total': 0}

            # Get all recipients
            recipients = self.get_all_recipients()
            if not recipients:
                logger.warning(f"No recipients found for broadcast {broadcast_id}")
                return {'sent': 0, 'failed': 0, 'total': 0}

            logger.info(f"Sending to {len(recipients)} recipients")

            stats = {
                'sent': 0,
                'failed': 0,
                'total': len(recipients)
            }

            # Collect all log entries for batch write
            log_entries = []

            # Send to each recipient
            for recipient in recipients:
                phone = recipient.get('Phone', '')
                name = recipient.get('Name', 'Customer')

                if not phone:
                    logger.warning(f"Skipping recipient with no phone: {name}")
                    stats['failed'] += 1
                    continue

                try:
                    # Send message with retry
                    logger.info(f"   Sending {msg_type} to {name} ({phone})")

                    success, retry_count = self._send_with_retry(
                        phone=phone,
                        parsed_message=parsed_message,
                        send_text_func=send_text_function,
                        send_image_func=send_image_function or (lambda p, u, c: False)
                    )

                    if success:
                        stats['sent'] += 1
                        # Delay between sends to avoid spam detection
                        if BROADCAST_DELAY_SECONDS > 0:
                            logger.info(f"      ⏳ Waiting {BROADCAST_DELAY_SECONDS}s before next send...")
                            time.sleep(BROADCAST_DELAY_SECONDS)
                        delivery_status = 'Delivered'
                        logger.info(f"      Sent successfully (retries: {retry_count})")
                    else:
                        stats['failed'] += 1
                        delivery_status = 'Failed'
                        logger.warning(f"      Failed after {retry_count} attempts")

                    # Collect log entry
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entries.append([
                        broadcast_id,
                        title,
                        phone,
                        name,
                        now,
                        delivery_status,
                        msg_type,
                        retry_count,
                        ''
                    ])

                except Exception as e:
                    logger.error(f"      Error sending to {phone}: {e}")
                    stats['failed'] += 1
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entries.append([
                        broadcast_id,
                        title,
                        phone,
                        name,
                        now,
                        'Error',
                        msg_type,
                        MAX_RETRY_ATTEMPTS,
                        str(e)[:100]
                    ])

            logger.info("="*80)
            logger.info(f"BROADCAST COMPLETE: {broadcast_id}")
            logger.info(f"   Type: {msg_type.upper()}")
            logger.info(f"   Sent: {stats['sent']}/{stats['total']}")
            logger.info(f"   Failed: {stats['failed']}/{stats['total']}")
            logger.info("="*80)

            # BATCH WRITE: Log all entries at once
            if log_entries:
                logger.info(f"Batch writing {len(log_entries)} log entries...")
                self._batch_log_broadcast_deliveries(log_entries)

            # Mark broadcast as sent
            self._mark_broadcast_sent(broadcast_id, stats['sent'])

            return stats

        except Exception as e:
            logger.error(f"Error sending broadcast: {e}")
            return {'sent': 0, 'failed': 0, 'total': 0}

    def _batch_log_broadcast_deliveries(self, log_entries: List[List]):
        """BATCH WRITE: Log multiple broadcast deliveries in a single API call"""
        try:
            if not log_entries:
                logger.info("   (no entries to log)")
                return

            logger.info(f"   Writing {len(log_entries)} rows to Broadcast Logs sheet...")
            throttle_if_busy()
            self.logs_sheet.append_rows(log_entries, value_input_option='RAW')
            track_api_call()
            logger.info(f"   Batch logged successfully ({len(log_entries)} entries with 1 API call)")
        except Exception as e:
            logger.error(f"Error batch logging broadcast deliveries: {e}")
            logger.info(f"   Falling back to individual logging...")
            for entry in log_entries:
                try:
                    throttle_if_busy()
                    self.logs_sheet.append_row(entry)
                    track_api_call()
                except Exception as e2:
                    logger.error(f"   Error logging individual entry: {e2}")

    def _mark_broadcast_sent(self, broadcast_id: str, sent_count: int):
        """Mark broadcast as sent or failed in Google Sheets."""
        try:
            throttle_if_busy()
            broadcasts = self.broadcasts_sheet.get_all_records()
            track_api_call()
            row_index = None

            for idx, record in enumerate(broadcasts, start=2):
                if record.get("Broadcast ID") == broadcast_id:
                    row_index = idx
                    break

            if not row_index:
                logger.error(f"Broadcast {broadcast_id} not found in sheet")
                return

            status_value = "Sent" if sent_count > 0 else "Failed"
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            throttle_if_busy()
            self.broadcasts_sheet.update(f"G{row_index}:J{row_index}", [[
                status_value,
                sent_count,
                "",
                now
            ]])
            track_api_call()

            logger.info(f"Broadcast {broadcast_id} marked as {status_value} ({sent_count} recipients)")

        except Exception as e:
            logger.error(f"Error marking broadcast as sent: {e}")

    def mark_response_received(self, phone: str, response_text: str) -> bool:
        """Mark that a recipient responded to a broadcast"""
        try:
            throttle_if_busy()
            logs = self.logs_sheet.get_all_records()
            track_api_call()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            row_index = None
            for idx in range(len(logs), 0, -1):
                record = logs[idx - 1]
                if record.get('Phone') == phone:
                    row_index = idx + 1
                    break

            if row_index:
                throttle_if_busy()
                self.logs_sheet.update(f'I{row_index}', [[response_text[:100]]])
                track_api_call()
                logger.info(f"Marked response from {phone}")
                return True

            return False

        except Exception as e:
            logger.error(f"Error marking response: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get overall broadcast system statistics"""
        try:
            throttle_if_busy()
            broadcasts = self.broadcasts_sheet.get_all_records()
            track_api_call()
            throttle_if_busy()
            logs = self.logs_sheet.get_all_records()
            track_api_call()

            stats = {
                'total_broadcasts': len(broadcasts),
                'pending': len([b for b in broadcasts if str(b.get('Status', '')).lower() == 'pending']),
                'sent': len([b for b in broadcasts if str(b.get('Status', '')).lower() == 'sent']),
                'total_messages_sent': sum(int(b.get('Sent Count', 0)) for b in broadcasts if b.get('Sent Count')),
                'text_messages': len([l for l in logs if l.get('Message Type') == 'text']),
                'image_messages': len([l for l in logs if l.get('Message Type') == 'image']),
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {}

    def add_recipient(self, name: str, phone: str, notes: str = '') -> bool:
        """Add a new recipient to the broadcast list"""
        try:
            throttle_if_busy()
            recipients = self.recipients_sheet.get_all_records()
            track_api_call()
            for recipient in recipients:
                if recipient.get('Phone') == phone:
                    logger.warning(f"Recipient {phone} already exists")
                    return False

            now = datetime.now().strftime('%Y-%m-%d')
            throttle_if_busy()
            self.recipients_sheet.append_row([
                name,
                phone,
                'Active',
                now,
                notes
            ])
            track_api_call()

            logger.info(f"Added recipient: {name} ({phone})")
            return True

        except Exception as e:
            logger.error(f"Error adding recipient: {e}")
            return False
