"""
Setup Booking Sheet Script
Automatically creates "Bookings" sheet in Google Sheets if it doesn't exist
Adds proper headers for booking tracking
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
setup_logging(log_dir='logs', agent_name='BookingSheetSetup')
logger = get_logger(__name__)


def setup_booking_sheet():
    """
    Setup Bookings sheet in Google Sheets
    - Creates sheet if it doesn't exist
    - Adds header row with proper columns
    - Validates existing sheet structure
    """
    logger.info("="*80)
    logger.info("BOOKING SHEET SETUP")
    logger.info("="*80)

    try:
        # Load config
        logger.info("Loading configuration...")
        config = load_config()

        # Get Google Sheets credentials
        credentials_file = config.get('lead_tracking.credentials_file', '<PUT_YOUR_GOOGLE_CREDENTIALS_PATH_HERE>')  # <-- put your Google credentials path here
        spreadsheet_name = config.get('lead_tracking.spreadsheet_name', '')

        if not os.path.exists(credentials_file):
            logger.error(f"❌ Credentials file not found: {credentials_file}")
            return False

        if not spreadsheet_name:
            logger.error("❌ Spreadsheet name not configured in config.json")
            return False

        logger.info(f"✓ Credentials file: {credentials_file}")
        logger.info(f"✓ Spreadsheet: {spreadsheet_name}")

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

        logger.info(f"✓ Connected to spreadsheet: {spreadsheet.title}")

        # Check if Bookings sheet exists
        logger.info("Checking for 'Bookings' sheet...")
        sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
        logger.info(f"Existing sheets: {', '.join(sheet_names)}")

        bookings_sheet = None

        if "Bookings" in sheet_names:
            logger.info("✓ 'Bookings' sheet already exists")
            bookings_sheet = spreadsheet.worksheet("Bookings")

            # Validate header row
            logger.info("Validating header row...")
            headers = bookings_sheet.row_values(1)

            expected_headers = [
                "Name",
                "Gender",
                "Phone",
                "Booking Date",
                "Booking Time",
                "Service",
                "Therapist Gender",
                "Timestamp"
            ]

            if headers == expected_headers:
                logger.info("✓ Header row is correct")
                logger.info("="*80)
                logger.info("✅ BOOKING SHEET SETUP COMPLETE")
                logger.info("="*80)
                return True
            else:
                logger.warning("⚠️ Header row needs updating")
                logger.warning(f"Current headers: {headers}")
                logger.warning(f"Expected headers: {expected_headers}")

                # Update header row
                logger.info("Updating header row...")
                bookings_sheet.update('A1:H1', [expected_headers])
                logger.info("✓ Header row updated")

        else:
            # Create new Bookings sheet
            logger.info("Creating new 'Bookings' sheet...")
            bookings_sheet = spreadsheet.add_worksheet(
                title="Bookings",
                rows=1000,
                cols=8
            )
            logger.info("✓ 'Bookings' sheet created")

            # Add header row
            logger.info("Adding header row...")
            headers = [
                "Name",
                "Gender",
                "Phone",
                "Booking Date",
                "Booking Time",
                "Service",
                "Therapist Gender",
                "Timestamp"
            ]
            bookings_sheet.update('A1:H1', [headers])
            logger.info("✓ Header row added")

            # Format header row (bold, background color)
            logger.info("Formatting header row...")
            bookings_sheet.format('A1:H1', {
                "backgroundColor": {
                    "red": 0.2,
                    "green": 0.8,
                    "blue": 0.4
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
            logger.info("✓ Header row formatted")

        # Display summary
        logger.info("="*80)
        logger.info("BOOKING SHEET STRUCTURE")
        logger.info("="*80)
        logger.info("Column A: Name              - Customer name")
        logger.info("Column B: Gender            - Male/Female")
        logger.info("Column C: Phone             - Customer phone number")
        logger.info("Column D: Booking Date      - Date of appointment")
        logger.info("Column E: Booking Time      - Time of appointment")
        logger.info("Column F: Service           - Service type and duration")
        logger.info("Column G: Therapist Gender  - Male/Female therapist")
        logger.info("Column H: Timestamp         - When booking was recorded")
        logger.info("="*80)
        logger.info("✅ BOOKING SHEET SETUP COMPLETE")
        logger.info("="*80)

        return True

    except Exception as e:
        logger.error("="*80)
        logger.error("❌ SETUP FAILED")
        logger.error("="*80)
        logger.error(f"Error: {str(e)}")
        logger.exception("Full error traceback:")
        return False


if __name__ == "__main__":
    print("\n" + "="*80)
    print("REFLEXOLOGY AGENT - BOOKING SHEET SETUP")
    print("="*80)
    print("This script will:")
    print("  1. Connect to your Google Sheets")
    print("  2. Create 'Bookings' sheet (if it doesn't exist)")
    print("  3. Add proper header columns")
    print("  4. Format the header row")
    print("="*80)
    print()

    # Check if running non-interactively
    import sys
    if sys.stdin.isatty():
        input("Press Enter to continue...")
        print()
    else:
        print("Running in non-interactive mode...\n")

    success = setup_booking_sheet()

    if success:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print("The 'Bookings' sheet is ready for booking tracking.")
        print()
        print("Next steps:")
        print("  1. Booking function will be added to lead_manager.py")
        print("  2. ChatAgent will detect booking confirmations")
        print("  3. Booking data will be automatically recorded")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ SETUP FAILED")
        print("="*80)
        print("Please check the logs for error details.")
        print("="*80)
        sys.exit(1)
