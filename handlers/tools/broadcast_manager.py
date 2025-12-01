"""
Broadcast Manager Tool
Manages scheduled promotional message broadcasts
Staff can add scheduled messages in Google Sheets and system auto-sends at scheduled time
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import json
from utils.logger import get_logger
from utils.rate_limiter import throttle_if_busy, track_api_call
from utils.cache_manager import CacheManager

logger = get_logger(__name__)


class BroadcastManager:
    """
    Manages scheduled broadcast messages for promotional campaigns
    Integrates with Google Sheets for broadcast management and tracking

    Features:
    - Staff adds recipients to "Broadcast Recipients" sheet
    - Staff schedules messages in "Scheduled Broadcasts" sheet
    - System auto-sends at scheduled time
    - Logs all deliveries in "Broadcast Logs" sheet
    """

    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """
        Initialize Broadcast Manager with Google Sheets connection

        Args:
            credentials_file: Path to Google service account JSON
            spreadsheet_name: Name/ID of Google Sheet to use
        """
        logger.info("🔧 Initializing Broadcast Manager...")

        # Define Google Sheets API scope
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]

        try:
            # Authenticate using service account
            logger.info(f"📝 Loading credentials from: {credentials_file}")
            credentials = Credentials.from_service_account_file(
                credentials_file,
                scopes=SCOPES
            )

            # Connect to Google Sheets
            self.gc = gspread.authorize(credentials)

            # Open spreadsheet
            logger.info(f"📊 Opening spreadsheet: {spreadsheet_name}")
            try:
                self.spreadsheet = self.gc.open(spreadsheet_name)
            except gspread.SpreadsheetNotFound:
                if 'docs.google.com/spreadsheets/d/' in spreadsheet_name:
                    self.spreadsheet = self.gc.open_by_url(spreadsheet_name)
                else:
                    self.spreadsheet = self.gc.open_by_key(spreadsheet_name)

            # Initialize sheets (create if don't exist)
            self._init_sheets()

            logger.info("✅ Broadcast Manager initialized successfully!")
            logger.info(f"   Spreadsheet: {spreadsheet_name}")
            logger.info(f"   Recipients Sheet: {self.recipients_sheet.title}")
            logger.info(f"   Broadcasts Sheet: {self.broadcasts_sheet.title}")
            logger.info(f"   Logs Sheet: {self.logs_sheet.title}")

        except FileNotFoundError:
            logger.error(f"❌ Credentials file not found: {credentials_file}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Broadcast Manager: {e}")
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
                "Delivery Status", "Response Received", "Response Time", "Response Text"
            ]
        }

        # Access or create each sheet
        for sheet_name, headers in sheets_config.items():
            try:
                worksheet = self.spreadsheet.worksheet(sheet_name)
                logger.info(f"   ✅ Found sheet: {sheet_name}")
            except gspread.WorksheetNotFound:
                logger.info(f"   ⚠️  Sheet not found: {sheet_name}, creating...")
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
                logger.info(f"   ✅ Created sheet: {sheet_name}")

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
            'sent_time': 4, 'delivery_status': 5, 'response_received': 6,
            'response_time': 7, 'response_text': 8
        }

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
            logger.info(f"📋 Found {len(active_recipients)} active recipients")
            return active_recipients
        except Exception as e:
            logger.error(f"❌ Error fetching recipients: {e}")
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
                    logger.debug(f"   ⏭️  {broadcast_id} missing date/time")
                    continue

                logger.debug(f"   Parsed date: '{schedule_date_str}', time: '{schedule_time_str}'")

                try:
                    # Parse schedule date and time
                    # Expected formats:
                    # Date: "2025-11-26" or "26/11/2025" or "2025-11-26"
                    # Time: "10:00" or "10:00:00"

                    # Try different date formats
                    schedule_datetime = None
                    for date_format in ['%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y']:
                        try:
                            date_obj = datetime.strptime(schedule_date_str, date_format)
                            # Parse time
                            if len(schedule_time_str.split(':')) == 2:
                                time_format = '%H:%M'
                            else:
                                time_format = '%H:%M:%S'
                            time_obj = datetime.strptime(schedule_time_str, time_format).time()

                            # Combine date and time
                            schedule_datetime = datetime.combine(date_obj.date(), time_obj)
                            logger.debug(f"   Successfully parsed datetime: {schedule_datetime}")
                            break
                        except ValueError:
                            continue

                    if not schedule_datetime:
                        logger.debug(f"   ❌ {broadcast_id}: Invalid date/time format: '{schedule_date_str}' '{schedule_time_str}'")
                        continue

                    # Check if scheduled time has passed
                    if schedule_datetime <= now:
                        pending.append(record)
                        logger.debug(f"   ✅ {broadcast_id} is ready to send (scheduled: {schedule_datetime}, now: {now})")
                    else:
                        logger.debug(f"   ⏱️ {broadcast_id} not yet ready (scheduled: {schedule_datetime}, now: {now})")

                except Exception as e:
                    logger.warning(f"⚠️  Error parsing schedule for {record.get('Broadcast ID')}: {e}")
                    continue

            logger.info(f"📬 Found {len(pending)} broadcasts ready to send")
            return pending

        except Exception as e:
            logger.error(f"❌ Error fetching pending broadcasts: {e}")
            return []

    def send_broadcast(self, broadcast: Dict[str, Any], send_function) -> Dict[str, Any]:
        """
        Send broadcast to all recipients with BATCH LOGGING optimization

        Args:
            broadcast: Broadcast record from sheet
            send_function: Function to send WhatsApp message (phone, message) -> bool

        Returns:
            dict with stats: {'sent': int, 'failed': int, 'total': int}
        """
        try:
            broadcast_id = broadcast.get('Broadcast ID', 'UNKNOWN')
            title = broadcast.get('Title', 'Untitled')
            message = broadcast.get('Message', '')

            logger.info("="*80)
            logger.info(f"📢 SENDING BROADCAST: {broadcast_id} - {title}")
            logger.info("="*80)

            if not message:
                logger.error(f"❌ Broadcast {broadcast_id} has no message content")
                return {'sent': 0, 'failed': 0, 'total': 0}

            # Get all recipients
            recipients = self.get_all_recipients()
            if not recipients:
                logger.warning(f"⚠️  No recipients found for broadcast {broadcast_id}")
                return {'sent': 0, 'failed': 0, 'total': 0}

            logger.info(f"📋 Sending to {len(recipients)} recipients")

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
                    logger.warning(f"⚠️  Skipping recipient with no phone: {name}")
                    stats['failed'] += 1
                    continue

                try:
                    # Send message via WhatsApp
                    logger.info(f"   📤 Sending to {name} ({phone})")
                    success = send_function(phone, message)

                    if success:
                        stats['sent'] += 1
                        delivery_status = 'Delivered'
                        logger.info(f"      ✅ Sent successfully")
                    else:
                        stats['failed'] += 1
                        delivery_status = 'Failed'
                        logger.warning(f"      ❌ Failed to send")

                    # Collect log entry (instead of writing immediately)
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entries.append([
                        broadcast_id,
                        title,
                        phone,
                        name,
                        now,
                        delivery_status,
                        'No',
                        '',
                        ''
                    ])

                except Exception as e:
                    logger.error(f"      ❌ Error sending to {phone}: {e}")
                    stats['failed'] += 1
                    # Collect log entry for error
                    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    log_entries.append([
                        broadcast_id,
                        title,
                        phone,
                        name,
                        now,
                        'Error',
                        'No',
                        '',
                        str(e)
                    ])

            logger.info("="*80)
            logger.info(f"📊 BROADCAST COMPLETE: {broadcast_id}")
            logger.info(f"   Sent: {stats['sent']}/{stats['total']}")
            logger.info(f"   Failed: {stats['failed']}/{stats['total']}")
            logger.info("="*80)

            # BATCH WRITE: Log all entries at once
            if log_entries:
                logger.info(f"📝 Batch writing {len(log_entries)} log entries...")
                self._batch_log_broadcast_deliveries(log_entries)

            # Mark broadcast as sent
            self._mark_broadcast_sent(broadcast_id, stats['sent'])

            return stats

        except Exception as e:
            logger.error(f"❌ Error sending broadcast: {e}")
            return {'sent': 0, 'failed': 0, 'total': 0}

    def _batch_log_broadcast_deliveries(self, log_entries: List[List]):
        """
        BATCH WRITE: Log multiple broadcast deliveries in a single API call

        This is significantly more efficient than logging individually:
        - 100 recipients: 100 API calls → 1 API call (99% reduction!)
        - Reduces quota consumption from ~356 to ~1 per broadcast

        Args:
            log_entries: List of log entry rows to append
        """
        try:
            if not log_entries:
                logger.info("   (no entries to log)")
                return

            logger.info(f"   📝 Writing {len(log_entries)} rows to Broadcast Logs sheet...")
            throttle_if_busy()
            self.logs_sheet.append_rows(log_entries, value_input_option='RAW')
            track_api_call()
            logger.info(f"   ✅ Batch logged successfully ({len(log_entries)} entries with 1 API call)")
        except Exception as e:
            logger.error(f"❌ Error batch logging broadcast deliveries: {e}")
            # Fallback: log individually if batch fails
            logger.info(f"   Falling back to individual logging...")
            for entry in log_entries:
                try:
                    throttle_if_busy()
                    self.logs_sheet.append_row(entry)
                    track_api_call()
                except Exception as e2:
                    logger.error(f"   ⚠️  Error logging individual entry: {e2}")

    def _log_broadcast_delivery(self, broadcast_id: str, title: str, phone: str,
                                name: str, delivery_status: str):
        """
        DEPRECATED: Use _batch_log_broadcast_deliveries() instead
        Log single broadcast delivery to Google Sheets (individual API call)
        """
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_entry = [
                broadcast_id,
                title,
                phone,
                name,
                now,
                delivery_status,
                'No',  # Response Received
                '',    # Response Time
                ''     # Response Text
            ]
            throttle_if_busy()
            self.logs_sheet.append_row(log_entry)
            track_api_call()
        except Exception as e:
            logger.error(f"⚠️  Error logging broadcast delivery: {e}")

    def _mark_broadcast_sent(self, broadcast_id: str, sent_count: int):
        """Mark broadcast as sent or failed in Google Sheets."""
        try:
            # Find the broadcast row
            throttle_if_busy()
            broadcasts = self.broadcasts_sheet.get_all_records()
            track_api_call()
            row_index = None

            for idx, record in enumerate(broadcasts, start=2):  # Start at 2 (skip header)
                if record.get("Broadcast ID") == broadcast_id:
                    row_index = idx
                    break

            if not row_index:
                logger.error(f"Broadcast {broadcast_id} not found in sheet")
                return

            # Decide status based on sent_count; if nothing delivered, mark as Failed for clarity
            status_value = "Sent" if sent_count > 0 else "Failed"

            # Update status and record sent count
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            throttle_if_busy()
            self.broadcasts_sheet.update(f"G{row_index}:J{row_index}", [[
                status_value,   # Status
                sent_count,     # Sent Count
                "",             # Created Date (keep existing)
                now             # Sent Date
            ]])
            track_api_call()

            logger.info(f"Broadcast {broadcast_id} marked as {status_value} ({sent_count} recipients)")

        except Exception as e:
            logger.error(f"Error marking broadcast as sent: {e}")
    def mark_response_received(self, phone: str, response_text: str) -> bool:
        """
        Mark that a recipient responded to a broadcast

        Args:
            phone: Recipient's phone number
            response_text: Their response message

        Returns:
            True if updated successfully
        """
        try:
            # Find most recent broadcast sent to this phone
            throttle_if_busy()
            logs = self.logs_sheet.get_all_records()
            track_api_call()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            # Search backwards to find most recent
            row_index = None
            for idx in range(len(logs), 0, -1):
                record = logs[idx - 1]
                if (record.get('Phone') == phone and
                    record.get('Response Received') == 'No'):
                    row_index = idx + 1  # +1 for header
                    break

            if row_index:
                throttle_if_busy()
                self.logs_sheet.update(f'G{row_index}:I{row_index}', [[
                    'Yes',                    # Response Received
                    now,                      # Response Time
                    response_text[:100]       # Response Text (truncated to 100 chars)
                ]])
                track_api_call()
                logger.info(f"✅ Marked response from {phone}")
                return True

            return False

        except Exception as e:
            logger.error(f"⚠️  Error marking response: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall broadcast system statistics

        Returns:
            Dictionary with stats
        """
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
                'total_responses': len([l for l in logs if l.get('Response Received') == 'Yes']),
                'response_rate': 0
            }

            # Calculate response rate
            if stats['total_messages_sent'] > 0:
                stats['response_rate'] = (stats['total_responses'] / stats['total_messages_sent']) * 100

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

    def add_recipient(self, name: str, phone: str, notes: str = '') -> bool:
        """
        Add a new recipient to the broadcast list

        Args:
            name: Recipient name
            phone: Recipient phone number
            notes: Optional notes

        Returns:
            True if added successfully
        """
        try:
            # Check if already exists
            throttle_if_busy()
            recipients = self.recipients_sheet.get_all_records()
            track_api_call()
            for recipient in recipients:
                if recipient.get('Phone') == phone:
                    logger.warning(f"⚠️  Recipient {phone} already exists")
                    return False

            # Add new recipient
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

            logger.info(f"✅ Added recipient: {name} ({phone})")
            return True

        except Exception as e:
            logger.error(f"❌ Error adding recipient: {e}")
            return False




