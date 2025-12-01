"""
Setup Script for Follow-up Campaign Sheets
Automatically creates the required Google Sheets tabs for the follow-up system
"""
import gspread
from google.oauth2.service_account import Credentials
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.logger import setup_logging, get_logger

setup_logging()
logger = get_logger(__name__)


def setup_followup_sheets(credentials_file: str, spreadsheet_name: str):
    """
    Create all required sheets for follow-up campaigns

    Args:
        credentials_file: Path to Google service account JSON
        spreadsheet_name: Name of Google Sheet to use
    """
    logger.info("="*80)
    logger.info("FOLLOW-UP CAMPAIGNS SHEET SETUP")
    logger.info("="*80)

    # Define Google Sheets API scope
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive.file'
    ]

    try:
        # Authenticate
        logger.info(f"📝 Loading credentials from: {credentials_file}")
        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES
        )

        # Connect to Google Sheets
        gc = gspread.authorize(credentials)

        # Open spreadsheet
        logger.info(f"📊 Opening spreadsheet: {spreadsheet_name}")
        try:
            spreadsheet = gc.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            if 'docs.google.com/spreadsheets/d/' in spreadsheet_name:
                spreadsheet = gc.open_by_url(spreadsheet_name)
            else:
                spreadsheet = gc.open_by_key(spreadsheet_name)

        logger.info(f"✅ Connected to: {spreadsheet.title}")

        # Define sheets to create
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

        # Create each sheet
        for sheet_name, headers in sheets_config.items():
            logger.info(f"\n📋 Setting up: {sheet_name}")

            # Check if sheet already exists
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                logger.info(f"   ⚠️  Sheet already exists, checking headers...")

                # Update headers if needed
                existing_headers = worksheet.row_values(1)
                if existing_headers != headers:
                    worksheet.update('A1', [headers])
                    logger.info(f"   ✅ Headers updated")
                else:
                    logger.info(f"   ✅ Headers correct, skipping")

            except gspread.WorksheetNotFound:
                # Sheet doesn't exist, create it
                logger.info(f"   Creating new sheet...")
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name,
                    rows=1000,
                    cols=len(headers)
                )

                # Add headers
                worksheet.update('A1', [headers])

                # Format header row (bold, frozen)
                worksheet.format('A1:Z1', {
                    "textFormat": {"bold": True},
                    "backgroundColor": {"red": 0.9, "green": 0.9, "blue": 0.9}
                })
                worksheet.freeze(rows=1)

                logger.info(f"   ✅ Sheet created with {len(headers)} columns")

        # Add sample campaign to help user get started
        logger.info(f"\n📝 Adding sample campaign...")
        campaigns_sheet = spreadsheet.worksheet("Follow-up Campaigns")

        # Check if sample already exists
        if len(campaigns_sheet.get_all_values()) == 1:  # Only header row
            sample_campaign = [
                "FU001",  # Campaign ID
                "3-Day No Response Follow-up",  # Campaign Name
                "no_response_72_hours",  # Target Condition
                "Hi! I noticed we chatted a few days ago about reflexology services. Are you still interested? 😊",  # Message 1
                "Hello again! We have a special promotion this week - 20% off your first session. Would you like to book?",  # Message 2
                "Last chance! Our promotion ends soon. Book now to save 20%!",  # Message 3
                "48",  # Gap Hours 1→2
                "72",  # Gap Hours 2→3
                "Paused",  # Status (paused by default for safety)
                "0",  # Total Sent
                "2024-11-17"  # Created Date
            ]
            campaigns_sheet.append_row(sample_campaign)
            logger.info(f"   ✅ Sample campaign added (Status: Paused)")
            logger.info(f"   💡 Edit the campaign and set Status to 'Active' to enable it")
        else:
            logger.info(f"   ⚠️  Campaigns already exist, skipping sample")

        logger.info("\n" + "="*80)
        logger.info("✅ SETUP COMPLETE!")
        logger.info("="*80)
        logger.info("\nNext steps:")
        logger.info("1. Review the sample campaign in 'Follow-up Campaigns' sheet")
        logger.info("2. Edit messages and timing as needed")
        logger.info("3. Change Status from 'Paused' to 'Active' to enable")
        logger.info("4. The system will start processing automatically")
        logger.info("\nFor more information, see: FOLLOW_UP_SETUP_GUIDE.md")

    except FileNotFoundError:
        logger.error(f"❌ Credentials file not found: {credentials_file}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Error during setup: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    # Load config to get spreadsheet details
    try:
        from core import load_config
        config = load_config()

        credentials_file = config.get('lead_tracking.credentials_file', '<PUT_YOUR_GOOGLE_CREDENTIALS_PATH_HERE>')  # <-- put your Google credentials path here
        spreadsheet_name = config.get('lead_tracking.spreadsheet_name', 'Customer record')

        logger.info(f"Using config:")
        logger.info(f"  Credentials: {credentials_file}")
        logger.info(f"  Spreadsheet: {spreadsheet_name}")

        setup_followup_sheets(credentials_file, spreadsheet_name)

    except Exception as e:
        logger.error(f"❌ Failed to load config: {e}")
        logger.info("\nUsage: python scripts/setup_followup_sheets.py")
        logger.info("Make sure config/config.json is configured correctly")
        sys.exit(1)
