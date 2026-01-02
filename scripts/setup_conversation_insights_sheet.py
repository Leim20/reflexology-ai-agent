"""
Setup Conversation Insights Sheet Script
Automatically creates "Conversation Insights" sheet in Google Sheets if it doesn't exist
Used for tracking customer pain points and AI recommendations
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import load_config
from utils.logger import setup_logging, get_logger
import gspread
from google.oauth2.service_account import Credentials

# Setup logging
setup_logging(log_dir='logs', agent_name='ConversationInsightsSetup')
logger = get_logger(__name__)


def setup_conversation_insights_sheet():
    """
    Setup Conversation Insights sheet in Google Sheets
    - Creates sheet if it doesn't exist
    - Adds header row with proper columns
    - Validates existing sheet structure
    """
    logger.info("="*80)
    logger.info("CONVERSATION INSIGHTS SHEET SETUP")
    logger.info("="*80)

    try:
        # Load config
        logger.info("Loading configuration...")
        config = load_config()

        # Get Google Sheets credentials
        credentials_file = config.get('lead_tracking.credentials_file', '<PUT_YOUR_GOOGLE_CREDENTIALS_PATH_HERE>')  # <-- put your Google credentials path here
        spreadsheet_name = config.get('lead_tracking.spreadsheet_name', '')

        if not os.path.exists(credentials_file):
            logger.error(f"Credentials file not found: {credentials_file}")
            return False

        if not spreadsheet_name:
            logger.error("Spreadsheet name not configured in config.json")
            return False

        logger.info(f"Credentials file: {credentials_file}")
        logger.info(f"Spreadsheet: {spreadsheet_name}")

        # Connect to Google Sheets
        logger.info("Connecting to Google Sheets...")
        SCOPES = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive.file'
        ]

        credentials = Credentials.from_service_account_file(
            credentials_file,
            scopes=SCOPES
        )
        gc = gspread.authorize(credentials)

        # Open spreadsheet
        try:
            spreadsheet = gc.open(spreadsheet_name)
        except gspread.SpreadsheetNotFound:
            if 'docs.google.com/spreadsheets/d/' in spreadsheet_name:
                spreadsheet = gc.open_by_url(spreadsheet_name)
            else:
                spreadsheet = gc.open_by_key(spreadsheet_name)

        logger.info(f"Connected to spreadsheet: {spreadsheet.title}")

        # Check if Conversation Insights sheet exists
        logger.info("Checking for 'Conversation Insights' sheet...")
        sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
        logger.info(f"Existing sheets: {', '.join(sheet_names)}")

        insights_sheet = None

        expected_headers = [
            "Phone",
            "Name",
            "Pain Points",
            "Recommendations",
            "Last Updated"
        ]

        if "Conversation Insights" in sheet_names:
            logger.info("'Conversation Insights' sheet already exists")
            insights_sheet = spreadsheet.worksheet("Conversation Insights")

            # Validate header row
            logger.info("Validating header row...")
            headers = insights_sheet.row_values(1)

            if headers == expected_headers:
                logger.info("Header row is correct")
                logger.info("="*80)
                logger.info("CONVERSATION INSIGHTS SHEET SETUP COMPLETE")
                logger.info("="*80)
                return True
            else:
                logger.warning("Header row needs updating")
                logger.warning(f"Current headers: {headers}")
                logger.warning(f"Expected headers: {expected_headers}")

                # Update header row
                logger.info("Updating header row...")
                insights_sheet.update('A1:E1', [expected_headers])
                logger.info("Header row updated")

        else:
            # Create new Conversation Insights sheet
            logger.info("Creating new 'Conversation Insights' sheet...")
            insights_sheet = spreadsheet.add_worksheet(
                title="Conversation Insights",
                rows=1000,
                cols=5
            )
            logger.info("'Conversation Insights' sheet created")

            # Add header row
            logger.info("Adding header row...")
            insights_sheet.update('A1:E1', [expected_headers])
            logger.info("Header row added")

            # Format header row (bold, background color)
            logger.info("Formatting header row...")
            insights_sheet.format('A1:E1', {
                "backgroundColor": {
                    "red": 0.4,
                    "green": 0.6,
                    "blue": 0.9
                },
                "textFormat": {
                    "bold": True,
                    "foregroundColor": {
                        "red": 1.0,
                        "green": 1.0,
                        "blue": 1.0
                    }
                },
                "horizontalAlignment": "CENTER"
            })
            logger.info("Header row formatted")

        # Display summary
        logger.info("="*80)
        logger.info("CONVERSATION INSIGHTS SHEET STRUCTURE")
        logger.info("="*80)
        logger.info("Column A: Phone           - Customer phone number")
        logger.info("Column B: Name            - Customer name")
        logger.info("Column C: Pain Points     - Customer's pain points/needs")
        logger.info("Column D: Recommendations - Services recommended by AI")
        logger.info("Column E: Last Updated    - Timestamp of last update")
        logger.info("="*80)
        logger.info("")
        logger.info("SPECIAL VALUES FOR PAIN POINTS:")
        logger.info("  - 'direct_booking_request' = Customer bypassed discovery")
        logger.info("  - 'not_disclosed' = Customer didn't share pain points")
        logger.info("="*80)
        logger.info("CONVERSATION INSIGHTS SHEET SETUP COMPLETE")
        logger.info("="*80)

        return True

    except Exception as e:
        logger.error("="*80)
        logger.error("SETUP FAILED")
        logger.error("="*80)
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("REFLEXOLOGY AGENT - CONVERSATION INSIGHTS SHEET SETUP")
    print("="*80)
    print("This script will:")
    print("  1. Connect to your Google Sheets")
    print("  2. Create 'Conversation Insights' sheet (if it doesn't exist)")
    print("  3. Add proper header columns")
    print("  4. Format the header row")
    print("="*80)
    print()
    print("PURPOSE:")
    print("  - Track customer pain points from conversations")
    print("  - Track AI recommendations made to customers")
    print("  - Enable warm lead detection (conversation but no booking)")
    print("="*80)
    print()

    # Check if running non-interactively
    import sys
    if sys.stdin.isatty():
        input("Press Enter to continue...")
        print()
    else:
        print("Running in non-interactive mode...\n")

    success = setup_conversation_insights_sheet()

    if success:
        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print("The 'Conversation Insights' sheet is ready for tracking.")
        print()
        print("How it works:")
        print("  1. AI makes a recommendation in STEP 3 of conversation")
        print("  2. track_conversation_info() is called automatically")
        print("  3. Pain points and recommendations are saved to sheet")
        print("  4. get_customer_context() checks for warm leads")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("SETUP FAILED")
        print("="*80)
        print("Please check the logs for error details.")
        print("="*80)
        sys.exit(1)
