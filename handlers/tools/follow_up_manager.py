"""
Follow-up Manager Tool
Manages automated follow-up campaigns for leads
Handles campaign enrollment, message scheduling, and analytics
"""
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Tuple
import json
from utils.logger import get_logger
from utils.cache_manager import CacheManager

logger = get_logger(__name__)


class FollowUpManager:
    """
    Manages automated follow-up campaigns for customer leads
    Integrates with Google Sheets for campaign management and tracking
    """

    def __init__(self, credentials_file: str, spreadsheet_name: str):
        """
        Initialize Follow-up Manager with Google Sheets connection

        Args:
            credentials_file: Path to Google service account JSON
            spreadsheet_name: Name of Google Sheet to use
        """
        logger.info("🔧 Initializing Follow-up Manager...")

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

            logger.info("✅ Follow-up Manager initialized successfully!")
            logger.info(f"   Spreadsheet: {spreadsheet_name}")
            logger.info(f"   Campaigns Sheet: {self.campaigns_sheet.title}")
            logger.info(f"   Queue Sheet: {self.queue_sheet.title}")

            # Initialize cache manager for campaign and queue caching
            logger.info("=" * 80)
            logger.info("Initializing CACHE MANAGER for Follow-up Manager...")
            self.cache_manager = CacheManager(default_ttl=300)  # 5 min cache
            logger.info("   Cache TTL: 300 seconds (campaign configurations)")
            logger.info("   Cache will reduce repeated campaign config reads")
            logger.info("CACHE MANAGER initialized successfully")
            logger.info("=" * 80)

        except FileNotFoundError:
            logger.info("=" * 80)
            logger.error(f"❌ Credentials file not found: {credentials_file}")
            raise
        except Exception as e:
            logger.error(f"❌ Failed to initialize Follow-up Manager: {e}")
            raise

    def _init_sheets(self):
        """Initialize all required sheets, create if they don't exist"""

        # Define sheet configurations
        sheets_config = {
            "Follow-up Campaigns": [
                "Campaign ID", "Campaign Name", "Target Condition",
                "Message 1", "Message 2", "Message 3",
                "Gap Hours 1→2", "Gap Hours 2→3", "Status",
                "Total Sent", "Created Date"
            ],
            "Follow-up Queue": [
                "Phone", "Campaign ID", "Current Message", "Next Send Time",
                "Status", "Enrolled Date", "Last Sent Date", "Messages Sent"
            ],
            "Follow-up Sent Log": [
                "Phone", "Campaign ID", "Campaign Name", "Message Number",
                "Message Text", "Sent Time", "Response Received",
                "Response Time", "Response Text"
            ],
            "Follow-up Analytics": [
                "Campaign ID", "Campaign Name", "Total Enrolled",
                "Message 1 Sent", "Message 2 Sent", "Message 3 Sent",
                "Responses Received", "Conversions", "Response Rate",
                "Conversion Rate", "Last Updated"
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
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
                worksheet.freeze(rows=1)
                logger.info(f"   ✅ Created sheet: {sheet_name}")

        # Store sheet references
        self.campaigns_sheet = self.spreadsheet.worksheet("Follow-up Campaigns")
        self.queue_sheet = self.spreadsheet.worksheet("Follow-up Queue")
        self.log_sheet = self.spreadsheet.worksheet("Follow-up Sent Log")
        self.analytics_sheet = self.spreadsheet.worksheet("Follow-up Analytics")

        # Column mappings for easier access
        self.campaign_cols = {
            'id': 0, 'name': 1, 'condition': 2,
            'msg1': 3, 'msg2': 4, 'msg3': 5,
            'gap1': 6, 'gap2': 7, 'status': 8,
            'total_sent': 9, 'created': 10
        }

        self.queue_cols = {
            'phone': 0, 'campaign_id': 1, 'current_msg': 2,
            'next_send': 3, 'status': 4, 'enrolled': 5,
            'last_sent': 6, 'msgs_sent': 7
        }

    def get_active_campaigns(self) -> List[Dict[str, Any]]:
        """
        Get all active campaigns from the sheet

        Returns:
            List of campaign dictionaries
        """
        try:
            records = self.campaigns_sheet.get_all_records()
            active_campaigns = [
                c for c in records
                if str(c.get('Status', '')).lower() == 'active'
            ]
            logger.info(f"📋 Found {len(active_campaigns)} active campaigns")
            return active_campaigns
        except Exception as e:
            logger.error(f"❌ Error fetching campaigns: {e}")
            return []

    def get_campaign_by_id(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific campaign by ID

        Args:
            campaign_id: Campaign identifier

        Returns:
            Campaign dict or None
        """
        try:
            records = self.campaigns_sheet.get_all_records()
            for campaign in records:
                if campaign.get('Campaign ID') == campaign_id:
                    return campaign
            return None
        except Exception as e:
            logger.error(f"❌ Error fetching campaign {campaign_id}: {e}")
            return None

    def enroll_lead_in_campaign(self, phone: str, campaign_id: str) -> bool:
        """
        Enroll a lead in a follow-up campaign

        Args:
            phone: Lead's phone number
            campaign_id: Campaign to enroll in

        Returns:
            True if enrolled successfully, False otherwise
        """
        try:
            # Check if lead is already enrolled in this campaign
            if self.is_lead_enrolled(phone, campaign_id):
                logger.info(f"   ⚠️  {phone} already enrolled in {campaign_id}")
                return False

            # Get campaign details
            campaign = self.get_campaign_by_id(campaign_id)
            if not campaign:
                logger.error(f"❌ Campaign not found: {campaign_id}")
                return False

            # Enroll lead
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            queue_entry = [
                phone,               # Phone
                campaign_id,         # Campaign ID
                1,                   # Current Message (start with 1)
                now,                 # Next Send Time (send immediately)
                'Pending',           # Status
                now,                 # Enrolled Date
                '',                  # Last Sent Date
                0                    # Messages Sent
            ]

            self.queue_sheet.append_row(queue_entry)
            logger.info(f"✅ Enrolled {phone} in campaign {campaign_id}")

            # Update analytics
            self._update_analytics_enrollment(campaign_id)

            return True

        except Exception as e:
            logger.error(f"❌ Error enrolling lead: {e}")
            return False

    def is_lead_enrolled(self, phone: str, campaign_id: str) -> bool:
        """
        Check if lead is already enrolled in a campaign

        Args:
            phone: Lead's phone number
            campaign_id: Campaign ID

        Returns:
            True if enrolled, False otherwise
        """
        try:
            records = self.queue_sheet.get_all_records()
            for record in records:
                if (record.get('Phone') == phone and
                    record.get('Campaign ID') == campaign_id and
                    record.get('Status') in ['Pending', 'Sent']):
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Error checking enrollment: {e}")
            return False

    def get_pending_followups(self) -> List[Dict[str, Any]]:
        """
        Get all follow-ups that are ready to be sent

        Returns:
            List of pending follow-up dictionaries
        """
        try:
            records = self.queue_sheet.get_all_records()
            now = datetime.now()

            pending = []
            for record in records:
                # Only process if status is Pending or Sent (waiting for next scheduled time)
                status = record.get('Status', '')
                if status not in ['Pending', 'Sent']:
                    continue

                # Check if it's time to send
                next_send_str = record.get('Next Send Time', '')
                if not next_send_str:
                    continue

                try:
                    next_send = datetime.strptime(next_send_str, '%Y-%m-%d %H:%M:%S')
                    if next_send <= now:
                        pending.append(record)
                except ValueError:
                    logger.warning(f"⚠️  Invalid date format: {next_send_str}")
                    continue

            logger.info(f"📬 Found {len(pending)} pending follow-ups")
            return pending

        except Exception as e:
            logger.error(f"❌ Error fetching pending follow-ups: {e}")
            return []

    def get_next_message(self, phone: str, campaign_id: str, lead_manager=None) -> Tuple[Optional[str], Optional[int]]:
        """
        Get the next message to send for a lead in a campaign
        Supports personalization with {name}, {pain_points}, {recommendations} placeholders

        Args:
            phone: Lead's phone number
            campaign_id: Campaign ID
            lead_manager: Optional LeadManager for personalization

        Returns:
            Tuple of (message_text, message_number) or (None, None)
        """
        try:
            # Get queue entry
            queue_records = self.queue_sheet.get_all_records()
            queue_entry = None
            for record in queue_records:
                if (record.get('Phone') == phone and
                    record.get('Campaign ID') == campaign_id):
                    queue_entry = record
                    break

            if not queue_entry:
                return None, None

            # Get campaign
            campaign = self.get_campaign_by_id(campaign_id)
            if not campaign:
                return None, None

            # Get current message number
            current_msg = int(queue_entry.get('Current Message', 1))

            # Get message text
            msg_key = f'Message {current_msg}'
            message_text = campaign.get(msg_key, '')

            if not message_text:
                logger.warning(f"No message {current_msg} for campaign {campaign_id}")
                return None, None

            # Personalization: Replace placeholders with actual data
            if lead_manager and ('{name}' in message_text or '{pain_points}' in message_text or '{recommendations}' in message_text):
                try:
                    # Get customer context for personalization
                    context = lead_manager.get_customer_context(phone)
                    conv_info = context.get('conversation_info', {})

                    # Get personalization data
                    name = conv_info.get('name', '')
                    if not name or name == 'Unknown':
                        # Try to get from customer memory
                        memory = lead_manager.get_customer_memory(phone)
                        if memory:
                            name = memory.get('name', '')

                    pain_points = conv_info.get('pain_points', '')
                    recommendations = conv_info.get('recommendations', '')

                    # Replace placeholders
                    if name and name != 'Unknown':
                        message_text = message_text.replace('{name}', name)
                    else:
                        message_text = message_text.replace('{name}', '')
                        message_text = message_text.replace('Hi {name}!', 'Hi!')
                        message_text = message_text.replace('Hi {name}', 'Hi')

                    if pain_points and pain_points not in ['direct_booking_request', 'not_disclosed']:
                        message_text = message_text.replace('{pain_points}', pain_points)
                    else:
                        message_text = message_text.replace('{pain_points}', 'your concerns')
                        message_text = message_text.replace('您{pain_points}', '您的需求')

                    if recommendations:
                        message_text = message_text.replace('{recommendations}', recommendations)
                    else:
                        message_text = message_text.replace('{recommendations}', 'our services')
                        message_text = message_text.replace('考虑{recommendations}', '考虑预约')

                    logger.info(f"Personalized message for {phone}: name={name}, pain={pain_points}, rec={recommendations}")

                except Exception as e:
                    logger.warning(f"Could not personalize message: {e}")
                    # Remove unfilled placeholders gracefully
                    message_text = message_text.replace('{name}', '')
                    message_text = message_text.replace('{pain_points}', 'your needs')
                    message_text = message_text.replace('{recommendations}', 'our services')

            return message_text, current_msg

        except Exception as e:
            logger.error(f"Error getting next message: {e}")
            return None, None

    def mark_followup_sent(self, phone: str, campaign_id: str, message_number: int, message_text: str) -> bool:
        """
        Mark a follow-up as sent and update queue/analytics

        Args:
            phone: Lead's phone number
            campaign_id: Campaign ID
            message_number: Which message was sent (1, 2, or 3)
            message_text: The message that was sent

        Returns:
            True if updated successfully
        """
        try:
            # Find and update queue entry
            queue_records = self.queue_sheet.get_all_records()
            row_index = None
            for idx, record in enumerate(queue_records, start=2):  # Start at 2 (skip header)
                if (record.get('Phone') == phone and
                    record.get('Campaign ID') == campaign_id):
                    row_index = idx
                    break

            if not row_index:
                logger.error(f"❌ Queue entry not found for {phone}, {campaign_id}")
                return False

            # Get campaign to calculate next send time
            campaign = self.get_campaign_by_id(campaign_id)
            if not campaign:
                return False

            # Calculate next send time
            now = datetime.now()
            now_str = now.strftime('%Y-%m-%d %H:%M:%S')

            if message_number < 3:
                # Schedule next message
                gap_key = f'Gap Hours {message_number}→{message_number + 1}'
                gap_hours = int(campaign.get(gap_key, 48))
                next_send = now + timedelta(hours=gap_hours)
                next_send_str = next_send.strftime('%Y-%m-%d %H:%M:%S')
                next_msg = message_number + 1
                status = 'Pending'
            else:
                # Campaign complete
                next_send_str = ''
                next_msg = 3
                status = 'Completed'

            # Update queue entry
            msgs_sent = message_number
            self.queue_sheet.update(f'C{row_index}:H{row_index}', [[
                next_msg,           # Current Message
                next_send_str,      # Next Send Time
                status,             # Status
                '',                 # Enrolled Date (keep existing)
                now_str,            # Last Sent Date
                msgs_sent           # Messages Sent
            ]])

            # Log to sent log
            campaign_name = campaign.get('Campaign Name', campaign_id)
            log_entry = [
                phone,
                campaign_id,
                campaign_name,
                message_number,
                message_text,
                now_str,
                'No',               # Response Received
                '',                 # Response Time
                ''                  # Response Text
            ]
            self.log_sheet.append_row(log_entry)

            # Update analytics
            self._update_analytics_sent(campaign_id, message_number)

            logger.info(f"✅ Marked message {message_number} as sent for {phone}")
            return True

        except Exception as e:
            logger.error(f"❌ Error marking follow-up as sent: {e}")
            return False

    def stop_campaign_for_lead(self, phone: str, campaign_id: str, reason: str = 'Responded') -> bool:
        """
        Stop a campaign for a specific lead

        Args:
            phone: Lead's phone number
            campaign_id: Campaign ID
            reason: Reason for stopping

        Returns:
            True if stopped successfully
        """
        try:
            # Find queue entry
            queue_records = self.queue_sheet.get_all_records()
            row_index = None
            for idx, record in enumerate(queue_records, start=2):
                if (record.get('Phone') == phone and
                    record.get('Campaign ID') == campaign_id):
                    row_index = idx
                    break

            if not row_index:
                return False

            # Update status
            self.queue_sheet.update(f'E{row_index}', reason)
            logger.info(f"✅ Stopped campaign {campaign_id} for {phone}: {reason}")
            return True

        except Exception as e:
            logger.error(f"❌ Error stopping campaign: {e}")
            return False

    def mark_lead_responded(self, phone: str, response_text: str) -> bool:
        """
        Mark that a lead responded (stops all active campaigns for this lead)

        Args:
            phone: Lead's phone number
            response_text: Their response message

        Returns:
            True if updated successfully
        """
        try:
            # Find all active campaigns for this lead
            queue_records = self.queue_sheet.get_all_records()
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            stopped_count = 0
            for idx, record in enumerate(queue_records, start=2):
                if (record.get('Phone') == phone and
                    record.get('Status') in ['Pending', 'Sent']):

                    # Stop this campaign
                    self.queue_sheet.update(f'E{idx}', 'Responded')
                    stopped_count += 1

                    # Update sent log if there's a recent message
                    campaign_id = record.get('Campaign ID')
                    self._update_log_response(phone, campaign_id, response_text, now)

            if stopped_count > 0:
                logger.info(f"✅ Stopped {stopped_count} campaigns for {phone} (responded)")
                return True
            return False

        except Exception as e:
            logger.error(f"❌ Error marking lead responded: {e}")
            return False

    def _update_log_response(self, phone: str, campaign_id: str, response_text: str, response_time: str):
        """Update the sent log with response information"""
        try:
            log_records = self.log_sheet.get_all_records()
            # Find most recent log entry for this phone/campaign
            row_index = None
            for idx in range(len(log_records), 0, -1):  # Search backwards
                record = log_records[idx - 1]
                if (record.get('Phone') == phone and
                    record.get('Campaign ID') == campaign_id and
                    record.get('Response Received') == 'No'):
                    row_index = idx + 1  # +1 for header
                    break

            if row_index:
                self.log_sheet.update(f'G{row_index}:I{row_index}', [[
                    'Yes',              # Response Received
                    response_time,      # Response Time
                    response_text[:100] # Response Text (truncated)
                ]])
        except Exception as e:
            logger.error(f"⚠️  Error updating log response: {e}")

    def _update_analytics_enrollment(self, campaign_id: str):
        """Update analytics when a lead is enrolled"""
        try:
            # Find or create analytics row for this campaign
            records = self.analytics_sheet.get_all_records()
            row_idx = None
            
            for idx, record in enumerate(records, start=2):
                if record.get('Campaign ID') == campaign_id:
                    row_idx = idx
                    break
            
            if row_idx:
                # Update existing row - increment Total Enrolled
                current_enrolled = int(self.analytics_sheet.cell(row_idx, 3).value or 0)
                self.analytics_sheet.update_cell(row_idx, 3, current_enrolled + 1)
                self.analytics_sheet.update_cell(row_idx, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
            else:
                # Create new analytics row
                campaign = self.get_campaign_by_id(campaign_id)
                campaign_name = campaign.get('Campaign Name', campaign_id) if campaign else campaign_id
                new_row = [
                    campaign_id,      # Campaign ID
                    campaign_name,    # Campaign Name
                    1,                # Total Enrolled
                    0, 0, 0,          # Message 1/2/3 Sent
                    0, 0,             # Responses, Conversions
                    '0%', '0%',       # Response Rate, Conversion Rate
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S')  # Last Updated
                ]
                self.analytics_sheet.append_row(new_row)
            
            logger.info(f"Analytics updated for enrollment in {campaign_id}")
        except Exception as e:
            logger.error(f"Error updating analytics enrollment: {e}")

    def _update_analytics_sent(self, campaign_id: str, message_number: int):
        """Update analytics when a message is sent"""
        try:
            records = self.analytics_sheet.get_all_records()
            row_idx = None
            
            for idx, record in enumerate(records, start=2):
                if record.get('Campaign ID') == campaign_id:
                    row_idx = idx
                    break
            
            if row_idx:
                # Update message sent count (columns 4, 5, 6 for msg 1, 2, 3)
                col = 3 + message_number  # Column D=4 for msg1, E=5 for msg2, F=6 for msg3
                current_sent = int(self.analytics_sheet.cell(row_idx, col).value or 0)
                self.analytics_sheet.update_cell(row_idx, col, current_sent + 1)
                self.analytics_sheet.update_cell(row_idx, 11, datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
                logger.info(f"Analytics updated: Message {message_number} sent for {campaign_id}")
        except Exception as e:
            logger.error(f"Error updating analytics sent: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get overall follow-up system statistics

        Returns:
            Dictionary with stats
        """
        try:
            queue_records = self.queue_sheet.get_all_records()

            stats = {
                'total_enrolled': len(queue_records),
                'active': len([r for r in queue_records if r.get('Status') == 'Pending']),
                'completed': len([r for r in queue_records if r.get('Status') == 'Completed']),
                'responded': len([r for r in queue_records if r.get('Status') == 'Responded']),
                'stopped': len([r for r in queue_records if r.get('Status') == 'Stopped'])
            }

            return stats

        except Exception as e:
            logger.error(f"❌ Error getting stats: {e}")
            return {}

    # ============================================================================
    # CONDITION CHECKING LOGIC
    # ============================================================================

    def check_lead_conditions(self, lead_data: Dict[str, Any], lead_manager=None) -> List[str]:
        """
        Check which follow-up conditions a lead meets

        Args:
            lead_data: Dictionary with lead information from LeadManager
                      Expected keys: phone, name, interest, last_updated, last_visit
            lead_manager: Optional LeadManager instance for warm_lead check

        Returns:
            List of condition codes that match (e.g., ['no_response_72_hours', 'warm_lead'])
        """
        try:
            conditions_met = []

            phone = lead_data.get('phone', '')
            interest = lead_data.get('interest', '')
            last_updated_str = lead_data.get('last_updated', '')
            last_visit_str = lead_data.get('last_visit', '')

            if not phone or not last_updated_str:
                return []

            # Parse last updated time
            try:
                last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d %H:%M:%S')
            except ValueError:
                # Try alternative format
                try:
                    last_updated = datetime.strptime(last_updated_str, '%Y-%m-%d')
                except ValueError:
                    logger.warning(f"⚠️  Invalid last_updated format: {last_updated_str}")
                    return []

            now = datetime.now()
            hours_since_update = (now - last_updated).total_seconds() / 3600

            # 1. Check NO RESPONSE conditions
            if hours_since_update >= 24:
                conditions_met.append('no_response_24_hours')

            if hours_since_update >= 72:
                conditions_met.append('no_response_72_hours')

            if hours_since_update >= 168:  # 7 days
                conditions_met.append('no_response_168_hours')

            # 2. Check NO BOOKING conditions
            # If interest contains "Booking" but no recent visit
            if 'booking' in interest.lower():
                if not last_visit_str or last_visit_str.lower() in ['', 'none', 'unknown']:
                    if hours_since_update >= 72:
                        conditions_met.append('no_booking_72_hours')

                    if hours_since_update >= 168:
                        conditions_met.append('no_booking_168_hours')

            # 3. Check NO PURCHASE AFTER VISIT
            # If they visited but interest is not booking/purchase
            if last_visit_str and last_visit_str.lower() not in ['', 'none', 'unknown']:
                # Check if visit was recent
                try:
                    last_visit = datetime.strptime(last_visit_str, '%Y-%m-%d')
                    days_since_visit = (now - last_visit).days

                    # If visited in last 30 days but no purchase indication
                    if days_since_visit <= 30:
                        if not any(keyword in interest.lower() for keyword in ['purchase', 'bought', 'paid', 'booked']):
                            conditions_met.append('no_purchase_after_visit')
                except ValueError:
                    pass

            # 4. Check NEW LEAD condition
            # If total conversations is low (e.g., 1-2)
            total_convs = lead_data.get('total_conversations', 0)
            if total_convs <= 2:
                conditions_met.append('new_lead')

            # 5. Check WARM LEAD condition (got recommendation but no booking)
            # Requires lead_manager to check Conversation Insights + Bookings sheets
            if lead_manager and hasattr(lead_manager, 'get_customer_context'):
                try:
                    context = lead_manager.get_customer_context(phone)
                    if context.get('is_warm_lead'):
                        # Check if enough time has passed (24 hours since last conversation)
                        conv_info = context.get('conversation_info', {})
                        last_updated_conv = conv_info.get('last_updated', '')
                        if last_updated_conv:
                            try:
                                conv_time = datetime.strptime(last_updated_conv, '%Y-%m-%d %H:%M:%S')
                                hours_since_conv = (datetime.now() - conv_time).total_seconds() / 3600
                                if hours_since_conv >= 24:
                                    conditions_met.append('warm_lead_24h')
                                if hours_since_conv >= 48:
                                    conditions_met.append('warm_lead_48h')
                                if hours_since_conv >= 72:
                                    conditions_met.append('warm_lead_72h')
                            except ValueError:
                                pass
                except Exception as e:
                    logger.warning(f"Could not check warm_lead condition: {e}")

            logger.info(f"📊 {phone} meets conditions: {conditions_met}")
            return conditions_met

        except Exception as e:
            logger.error(f"❌ Error checking lead conditions: {e}")
            return []

    def check_and_enroll_leads(self, lead_manager) -> Dict[str, Any]:
        """
        Check all leads and auto-enroll them in matching campaigns

        Args:
            lead_manager: LeadManager instance to get lead data

        Returns:
            Dictionary with enrollment stats
        """
        try:
            logger.info("="*60)
            logger.info("🔍 CHECKING LEADS FOR CAMPAIGN ENROLLMENT")
            logger.info("="*60)

            # Get all active campaigns
            campaigns = self.get_active_campaigns()
            if not campaigns:
                logger.info("⚠️  No active campaigns found")
                return {'enrolled': 0, 'skipped': 0}

            logger.info(f"📋 Found {len(campaigns)} active campaigns")

            # Get all leads from LeadManager
            all_leads = lead_manager.get_all_leads()
            if not all_leads:
                logger.info("⚠️  No leads found")
                return {'enrolled': 0, 'skipped': 0}

            logger.info(f"👥 Checking {len(all_leads)} leads")

            stats = {
                'enrolled': 0,
                'skipped': 0,
                'campaigns_triggered': {}
            }

            # Check each lead
            for lead in all_leads:
                phone = lead.get('phone', '')
                if not phone:
                    continue

                # Check which conditions this lead meets
                conditions = self.check_lead_conditions(lead, lead_manager)

                if not conditions:
                    stats['skipped'] += 1
                    continue

                # Find matching campaigns
                for campaign in campaigns:
                    campaign_id = campaign.get('Campaign ID')
                    target_condition = campaign.get('Target Condition')

                    # Check if lead meets this campaign's condition
                    if target_condition in conditions:
                        # Try to enroll
                        if self.enroll_lead_in_campaign(phone, campaign_id):
                            stats['enrolled'] += 1
                            if campaign_id not in stats['campaigns_triggered']:
                                stats['campaigns_triggered'][campaign_id] = 0
                            stats['campaigns_triggered'][campaign_id] += 1
                        else:
                            stats['skipped'] += 1

            logger.info("="*60)
            logger.info(f"✅ Enrollment complete:")
            logger.info(f"   Enrolled: {stats['enrolled']}")
            logger.info(f"   Skipped: {stats['skipped']}")
            logger.info(f"   Campaigns triggered: {stats['campaigns_triggered']}")
            logger.info("="*60)

            return stats

        except Exception as e:
            logger.error(f"❌ Error checking and enrolling leads: {e}")
            return {'enrolled': 0, 'skipped': 0}



    def check_warm_leads_from_insights(self, lead_manager) -> Dict[str, Any]:
        """
        Check Conversation Insights sheet for warm leads and enroll them.
        This catches leads that might not be in Customer Record but have conversation data.

        Args:
            lead_manager: LeadManager instance

        Returns:
            Dictionary with enrollment stats
        """
        try:
            logger.info("="*60)
            logger.info("🔍 CHECKING WARM LEADS FROM CONVERSATION INSIGHTS")
            logger.info("="*60)

            if not hasattr(lead_manager, 'conversation_insights_sheet') or not lead_manager.conversation_insights_sheet:
                logger.warning("Conversation Insights sheet not available")
                return {'enrolled': 0, 'skipped': 0}

            # Get active warm_lead campaigns
            campaigns = self.get_active_campaigns()
            warm_lead_campaigns = [c for c in campaigns if 'warm_lead' in c.get('Target Condition', '')]

            if not warm_lead_campaigns:
                logger.info("No warm_lead campaigns found - skipping")
                return {'enrolled': 0, 'skipped': 0}

            logger.info(f"Found {len(warm_lead_campaigns)} warm_lead campaigns")

            # Get all conversation insights
            insights = lead_manager.conversation_insights_sheet.get_all_records()
            logger.info(f"Checking {len(insights)} conversation records")

            stats = {'enrolled': 0, 'skipped': 0}

            for insight in insights:
                phone = insight.get('Phone', '')
                if not phone:
                    continue

                # Check if already followed up
                followup_status = insight.get('Followup Status', '')
                if followup_status in ['Sent', 'Responded', 'Booked']:
                    stats['skipped'] += 1
                    continue

                # Check warm lead status
                context = lead_manager.get_customer_context(phone)
                if not context.get('is_warm_lead'):
                    stats['skipped'] += 1
                    continue

                # Check timing
                last_updated = insight.get('Last Updated', '')
                if not last_updated:
                    continue

                try:
                    conv_time = datetime.strptime(last_updated, '%Y-%m-%d %H:%M:%S')
                    hours_since = (datetime.now() - conv_time).total_seconds() / 3600
                except ValueError:
                    continue

                # Match with campaigns
                for campaign in warm_lead_campaigns:
                    target = campaign.get('Target Condition', '')
                    campaign_id = campaign.get('Campaign ID')

                    # Check if hours match the campaign condition
                    should_enroll = False
                    if target == 'warm_lead_24h' and hours_since >= 24:
                        should_enroll = True
                    elif target == 'warm_lead_48h' and hours_since >= 48:
                        should_enroll = True
                    elif target == 'warm_lead_72h' and hours_since >= 72:
                        should_enroll = True
                    elif target == 'warm_lead' and hours_since >= 24:  # Default 24h
                        should_enroll = True

                    if should_enroll:
                        if self.enroll_lead_in_campaign(phone, campaign_id):
                            stats['enrolled'] += 1
                            logger.info(f"Enrolled warm lead {phone} in {campaign_id}")
                        else:
                            stats['skipped'] += 1

            logger.info(f"Warm lead check complete: enrolled={stats['enrolled']}, skipped={stats['skipped']}")
            return stats

        except Exception as e:
            logger.error(f"Error checking warm leads: {e}")
            return {'enrolled': 0, 'skipped': 0}

    # ============================================================================
    # BATCH OPERATIONS FOR MINIMAL QUOTA SYSTEM
    # ============================================================================

    def batch_mark_status_queued(self, messages: List[Dict[str, Any]]) -> bool:
        """
        Batch update status for multiple messages to 'Queued'

        Called by check job after adding messages to in-memory queue
        Marks them so they won't be checked again until processing is done

        Args:
            messages: List of message dicts with 'Phone' and 'Campaign ID'

        Returns:
            True if update successful
        """
        try:
            if not messages:
                return True

            # Get all queue records with row indices
            records = self.queue_sheet.get_all_records()

            # Build mapping of (phone, campaign_id) -> row_index
            message_rows = {}
            for idx, record in enumerate(records, start=2):  # Start at 2 (skip header)
                key = (record.get('Phone'), record.get('Campaign ID'))
                message_rows[key] = idx

            # Update status to 'Queued' for each message
            updates = []
            for msg in messages:
                phone = msg.get('Phone')
                campaign_id = msg.get('Campaign ID')
                key = (phone, campaign_id)

                if key in message_rows:
                    row_idx = message_rows[key]
                    # Status is column E (5)
                    updates.append({
                        'range': f'E{row_idx}',
                        'values': [['Queued']]
                    })

            # Batch update (gspread batch_update)
            if updates:
                self.queue_sheet.batch_update(updates)
                logger.info(f"✅ Batch marked {len(updates)} messages as 'Queued'")
                return True

            return True

        except Exception as e:
            logger.error(f"❌ Error batch marking status: {e}")
            return False

    def batch_update_queue(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Batch update multiple queue entries after messages are sent

        Args:
            updates: List of dicts with:
                - phone: str
                - campaign_id: str
                - message_num: int (just sent)
                - status: str ('Sent' or 'Failed')

        Returns:
            True if successful
        """
        try:
            if not updates:
                return True

            # Get all queue records with row indices
            records = self.queue_sheet.get_all_records()

            # Build mapping of (phone, campaign_id) -> (row_index, record)
            message_rows = {}
            for idx, record in enumerate(records, start=2):  # Start at 2 (skip header)
                key = (record.get('Phone'), record.get('Campaign ID'))
                message_rows[key] = (idx, record)

            # Prepare batch update
            batch_updates = []
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for update in updates:
                phone = update.get('phone')
                campaign_id = update.get('campaign_id')
                message_num = update.get('message_num')
                status = update.get('status', 'Sent')
                key = (phone, campaign_id)

                if key not in message_rows:
                    logger.warning(f"⚠️  Queue entry not found: {phone}, {campaign_id}")
                    continue

                row_idx, record = message_rows[key]

                # Get campaign to calculate next send time
                campaign = self.get_campaign_by_id(campaign_id)
                if not campaign:
                    logger.warning(f"⚠️  Campaign not found: {campaign_id}")
                    continue

                # Calculate next send time
                if message_num < 3:
                    gap_key = f'Gap Hours {message_num}→{message_num + 1}'
                    gap_hours = int(campaign.get(gap_key, 48))
                    next_send = datetime.now() + timedelta(hours=gap_hours)
                    next_send_str = next_send.strftime('%Y-%m-%d %H:%M:%S')
                    next_msg = message_num + 1
                    # Status: 'Sent' means message sent, waiting for next scheduled time
                    final_status = 'Sent'
                else:
                    next_send_str = ''
                    next_msg = 3
                    # Status: 'Completed' means all messages in campaign sent
                    final_status = 'Completed'

                # Update individual columns to avoid offset issues with empty Enrolled Date
                # C = Current Message, D = Next Send Time, E = Status, F = Enrolled Date (skip), G = Last Sent Date, H = Messages Sent
                batch_updates.append({'range': f'C{row_idx}', 'values': [[next_msg]]})
                batch_updates.append({'range': f'D{row_idx}', 'values': [[next_send_str]]})
                batch_updates.append({'range': f'E{row_idx}', 'values': [[final_status]]})
                # Skip F (Enrolled Date - keep existing)
                batch_updates.append({'range': f'G{row_idx}', 'values': [[now]]})
                batch_updates.append({'range': f'H{row_idx}', 'values': [[message_num]]})

            # Execute batch update
            if batch_updates:
                self.queue_sheet.batch_update(batch_updates)
                logger.info(f"✅ Batch updated {len(batch_updates)} queue entries")
                return True

            return True

        except Exception as e:
            logger.error(f"❌ Error batch updating queue: {e}")
            return False

    def batch_append_logs(self, updates: List[Dict[str, Any]]) -> bool:
        """
        Batch append multiple entries to the sent log

        Args:
            updates: List of dicts with:
                - phone: str
                - campaign_id: str
                - campaign_name: str (optional, will fetch if missing)
                - message_num: int
                - message_text: str
                - status: str ('Sent' or 'Failed')
                - error: str (optional, error message if failed)

        Returns:
            True if successful
        """
        try:
            if not updates:
                return True

            log_entries = []
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            for update in updates:
                phone = update.get('phone')
                campaign_id = update.get('campaign_id')
                message_num = update.get('message_num')
                message_text = update.get('message_text')
                status = update.get('status', 'Sent')

                # Get campaign name
                campaign_name = update.get('campaign_name')
                if not campaign_name:
                    campaign = self.get_campaign_by_id(campaign_id)
                    campaign_name = campaign.get('Campaign Name', campaign_id) if campaign else campaign_id

                # Build log entry
                if status == 'Sent':
                    log_entry = [
                        phone,
                        campaign_id,
                        campaign_name,
                        message_num,
                        message_text,
                        now,
                        'No',               # Response Received
                        '',                 # Response Time
                        ''                  # Response Text
                    ]
                else:
                    # Failed status
                    error = update.get('error', 'Unknown error')
                    log_entry = [
                        phone,
                        campaign_id,
                        campaign_name,
                        message_num,
                        f"[FAILED] {message_text}",
                        now,
                        'Failed',
                        '',
                        error
                    ]

                log_entries.append(log_entry)

            # Batch append to log sheet
            if log_entries:
                self.log_sheet.batch_update([
                    {'range': 'A:I', 'values': log_entries}
                ])
                logger.info(f"✅ Batch appended {len(log_entries)} log entries")
                return True

            return True

        except Exception as e:
            logger.error(f"❌ Error batch appending logs: {e}")
            return False
