"""
Setup Cancellation Log Sheet Script
Automatically creates "Cancellation Log" sheet in Google Sheets if it doesn't exist
Used for tracking cancellation reasons and outcomes for analytics
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
setup_logging(log_dir='logs', agent_name='CancellationLogSetup')
logger = get_logger(__name__)


def setup_cancellation_log_sheet():
    """
    Setup Cancellation Log sheet in Google Sheets
    - Creates sheet if it doesn't exist
    - Adds header row with proper columns
    - Validates existing sheet structure
    """
    logger.info("="*80)
    logger.info("CANCELLATION LOG SHEET SETUP")
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

        # Check if Cancellation Log sheet exists
        logger.info("Checking for 'Cancellation Log' sheet...")
        sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
        logger.info(f"Existing sheets: {', '.join(sheet_names)}")

        cancellation_sheet = None

        expected_headers = [
            "Phone",
            "Name",
            "Original Date",
            "Original Time",
            "Reason",
            "Outcome",
            "Notes",
            "Timestamp"
        ]

        if "Cancellation Log" in sheet_names:
            logger.info("'Cancellation Log' sheet already exists")
            cancellation_sheet = spreadsheet.worksheet("Cancellation Log")

            # Validate header row
            logger.info("Validating header row...")
            headers = cancellation_sheet.row_values(1)

            if headers == expected_headers:
                logger.info("Header row is correct")
                logger.info("="*80)
                logger.info("CANCELLATION LOG SHEET SETUP COMPLETE")
                logger.info("="*80)
                return True
            else:
                logger.warning("Header row needs updating")
                logger.warning(f"Current headers: {headers}")
                logger.warning(f"Expected headers: {expected_headers}")

                # Update header row
                logger.info("Updating header row...")
                cancellation_sheet.update('A1:H1', [expected_headers])
                logger.info("Header row updated")

        else:
            # Create new Cancellation Log sheet
            logger.info("Creating new 'Cancellation Log' sheet...")
            cancellation_sheet = spreadsheet.add_worksheet(
                title="Cancellation Log",
                rows=1000,
                cols=8
            )
            logger.info("'Cancellation Log' sheet created")

            # Add header row
            logger.info("Adding header row...")
            cancellation_sheet.update('A1:H1', [expected_headers])
            logger.info("Header row added")

            # Format header row (bold, background color)
            logger.info("Formatting header row...")
            cancellation_sheet.format('A1:H1', {
                "backgroundColor": {
                    "red": 0.9,
                    "green": 0.5,
                    "blue": 0.5
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
        logger.info("CANCELLATION LOG SHEET STRUCTURE")
        logger.info("="*80)
        logger.info("Column A: Phone          - Customer phone number")
        logger.info("Column B: Name           - Customer name")
        logger.info("Column C: Original Date  - Original booking date")
        logger.info("Column D: Original Time  - Original booking time")
        logger.info("Column E: Reason         - Cancellation reason")
        logger.info("Column F: Outcome        - rescheduled or cancelled")
        logger.info("Column G: Notes          - Additional notes")
        logger.info("Column H: Timestamp      - When logged")
        logger.info("="*80)
        logger.info("")
        logger.info("CANCELLATION REASONS:")
        logger.info("  - 'busy'       = Customer has something else to do")
        logger.info("  - 'health'     = Customer not feeling well")
        logger.info("  - 'budget'     = Budget/money concern")
        logger.info("  - 'reschedule' = Changed to different time")
        logger.info("  - 'other'      = Other reasons")
        logger.info("="*80)
        logger.info("")
        logger.info("OUTCOMES:")
        logger.info("  - 'rescheduled' = Customer changed to new time")
        logger.info("  - 'cancelled'   = Booking fully cancelled")
        logger.info("="*80)
        logger.info("CANCELLATION LOG SHEET SETUP COMPLETE")
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
    print("REFLEXOLOGY AGENT - CANCELLATION LOG SHEET SETUP")
    print("="*80)
    print("This script will:")
    print("  1. Connect to your Google Sheets")
    print("  2. Create 'Cancellation Log' sheet (if it doesn't exist)")
    print("  3. Add proper header columns")
    print("  4. Format the header row")
    print("="*80)
    print()
    print("PURPOSE:")
    print("  - Track cancellation reasons (busy, health, budget, etc.)")
    print("  - Track outcomes (rescheduled vs cancelled)")
    print("  - Enable analytics on cancellation patterns")
    print("  - Improve retention strategies")
    print("="*80)
    print()

    # Check if running non-interactively
    import sys
    if sys.stdin.isatty():
        input("Press Enter to continue...")
        print()
    else:
        print("Running in non-interactive mode...\n")

    success = setup_cancellation_log_sheet()

    if success:
        print("\n" + "="*80)
        print("SUCCESS!")
        print("="*80)
        print("The 'Cancellation Log' sheet is ready for tracking.")
        print()
        print("How it works:")
        print("  1. Customer requests to cancel booking")
        print("  2. AI asks about concerns with caring tone")
        print("  3. Based on reason, AI offers reschedule or accepts cancel")
        print("  4. log_cancellation_reason() is called automatically")
        print("  5. Reason and outcome saved to this sheet")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("SETUP FAILED")
        print("="*80)
        print("Please check the logs for error details.")
        print("="*80)
        sys.exit(1)
