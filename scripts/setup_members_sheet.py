"""
Setup Members Sheet Script
Automatically creates "Members" sheet in Google Sheets if it doesn't exist
Adds proper headers for member registration tracking
"""

import sys
import os
from pathlib import Path

# Add parent directory to path to import from core
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config_loader import load_config
from handlers.tools.lead_manager import LeadManager
from utils.logger import setup_logging, get_logger
import gspread
from google.oauth2.service_account import Credentials

# Setup logging
setup_logging(log_dir='logs', agent_name='MembersSheetSetup')
logger = get_logger(__name__)


def setup_members_sheet():
    """
    Setup Members sheet in Google Sheets
    - Creates sheet if it doesn't exist
    - Adds header row with proper columns
    - Validates existing sheet structure
    """
    logger.info("="*80)
    logger.info("MEMBERS SHEET SETUP")
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

        # Check if Members sheet exists
        logger.info("Checking for 'Members' sheet...")
        sheet_names = [sheet.title for sheet in spreadsheet.worksheets()]
        logger.info(f"Existing sheets: {', '.join(sheet_names)}")

        members_sheet = None

        if "Members" in sheet_names:
            logger.info("✓ 'Members' sheet already exists")
            members_sheet = spreadsheet.worksheet("Members")

            # Validate header row
            logger.info("Validating header row...")
            headers = members_sheet.row_values(1)

            expected_headers = [
                "Phone",
                "Name",
                "Birthday",
                "Registration Date",
                "Points",
                "Birthday Benefit Used This Year"
            ]

            if headers == expected_headers:
                logger.info("✓ Header row is correct")
                logger.info("="*80)
                logger.info("✅ MEMBERS SHEET SETUP COMPLETE")
                logger.info("="*80)
                return True
            else:
                logger.warning("⚠️ Header row needs updating")
                logger.warning(f"Current headers: {headers}")
                logger.warning(f"Expected headers: {expected_headers}")

                # Update header row
                logger.info("Updating header row...")
                members_sheet.update('A1:F1', [expected_headers])
                logger.info("✓ Header row updated")

        else:
            # Create new Members sheet
            logger.info("Creating new 'Members' sheet...")
            members_sheet = spreadsheet.add_worksheet(
                title="Members",
                rows=1000,
                cols=6
            )
            logger.info("✓ 'Members' sheet created")

            # Add header row
            logger.info("Adding header row...")
            headers = [
                "Phone",
                "Name",
                "Birthday",
                "Registration Date",
                "Points",
                "Birthday Benefit Used This Year"
            ]
            members_sheet.update('A1:F1', [headers])
            logger.info("✓ Header row added")

            # Format header row (bold, background color)
            logger.info("Formatting header row...")
            members_sheet.format('A1:F1', {
                "backgroundColor": {
                    "red": 0.2,
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
            logger.info("✓ Header row formatted")

        # Display summary
        logger.info("="*80)
        logger.info("MEMBERS SHEET STRUCTURE")
        logger.info("="*80)
        logger.info("Column A: Phone               - Customer phone number (unique identifier)")
        logger.info("Column B: Name                - Customer name")
        logger.info("Column C: Birthday            - Birthday in YYYY-MM-DD format")
        logger.info("Column D: Registration Date   - When they registered as member")
        logger.info("Column E: Points              - Loyalty points balance")
        logger.info("Column F: Birthday Benefit    - 'Yes' if used this year, 'No' if not")
        logger.info("="*80)
        logger.info("✅ MEMBERS SHEET SETUP COMPLETE")
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
    print("REFLEXOLOGY AGENT - MEMBERS SHEET SETUP")
    print("="*80)
    print("This script will:")
    print("  1. Connect to your Google Sheets")
    print("  2. Create 'Members' sheet (if it doesn't exist)")
    print("  3. Add proper header columns")
    print("  4. Format the header row")
    print("="*80)
    print()

    # Check if running non-interactively (e.g., via automated script)
    import sys
    if sys.stdin.isatty():
        input("Press Enter to continue...")
        print()
    else:
        print("Running in non-interactive mode...\n")

    success = setup_members_sheet()

    if success:
        print("\n" + "="*80)
        print("✅ SUCCESS!")
        print("="*80)
        print("The 'Members' sheet is ready for member registration.")
        print()
        print("Next steps:")
        print("  1. Member functions will be added to lead_manager.py")
        print("  2. ChatAgent will check member status before sending templates")
        print("  3. Registration logic will extract Name + Phone + Birthday")
        print("="*80)
        sys.exit(0)
    else:
        print("\n" + "="*80)
        print("❌ SETUP FAILED")
        print("="*80)
        print("Please check the logs for error details.")
        print("Common issues:")
        print("  - Google credentials file missing")
        print("  - Spreadsheet not shared with service account")
        print("  - Invalid spreadsheet name/URL")
        print("="*80)
        sys.exit(1)
