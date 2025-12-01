"""
Setup Google Sheets for Broadcast System
Creates the required sheets for scheduled broadcast messaging

Run this script once to initialize the broadcast sheets
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from handlers.tools.broadcast_manager import BroadcastManager
from datetime import datetime

def main():
    """Initialize broadcast Google Sheets"""

    print("="*80)
    print("BROADCAST SHEETS SETUP")
    print("="*80)
    print()

    # Get credentials and spreadsheet from config
    credentials_file = "config/<PUT_YOUR_GOOGLE_PROJECT_ID_HERE>-c123857bd130.json"  # <-- put your Google project ID here
    spreadsheet_name = "YOUR_GOOGLE_SHEET_ID"

    print(f"📁 Credentials: {credentials_file}")
    print(f"📊 Spreadsheet: {spreadsheet_name}")
    print()

    try:
        # Initialize Broadcast Manager (this will create sheets if they don't exist)
        print("🔧 Initializing Broadcast Manager...")
        print()

        broadcast_manager = BroadcastManager(
            credentials_file=credentials_file,
            spreadsheet_name=spreadsheet_name
        )

        print()
        print("="*80)
        print("✅ BROADCAST SHEETS SETUP COMPLETE!")
        print("="*80)
        print()
        print("📋 Created/Verified Sheets:")
        print("   1. Broadcast Recipients   - Add customer names & phone numbers here")
        print("   2. Scheduled Broadcasts   - Add promotional messages with schedule time")
        print("   3. Broadcast Logs         - Automatic delivery tracking")
        print()
        print("="*80)
        print("📝 NEXT STEPS:")
        print("="*80)
        print()
        print("1. Open your Google Sheet:")
        print("   https://docs.google.com/spreadsheets/d/YOUR_GOOGLE_SHEET_ID")
        print()
        print("2. Add Recipients:")
        print("   Go to 'Broadcast Recipients' sheet")
        print("   Add rows with: Name, Phone, Status (Active), Added Date, Notes")
        print("   Example:")
        print("   | Name     | Phone       | Status | Added Date | Notes      |")
        print("   | John Lee | 60123456789 | Active | 2025-11-26 | VIP Member |")
        print()
        print("3. Schedule a Broadcast:")
        print("   Go to 'Scheduled Broadcasts' sheet")
        print("   Add a row with your promotional message")
        print("   Example:")
        print("   | Broadcast ID | Title              | Message                           | Schedule Date | Schedule Time | Target List    | Status  |")
        print("   | BC001        | Weekend Promotion  | Weekend special: RM99 for 90min!  | 2025-11-27    | 10:00         | All Recipients | Pending |")
        print()
        print("4. System will auto-send at scheduled time!")
        print("   Check 'Broadcast Logs' sheet to see delivery status")
        print()
        print("="*80)
        print("💡 TIPS:")
        print("="*80)
        print()
        print("• Date format: YYYY-MM-DD (e.g., 2025-11-27)")
        print("• Time format: HH:MM (e.g., 10:00 or 14:30)")
        print("• Status must be 'Pending' for broadcasts to send")
        print("• Target List: Currently only 'All Recipients' is supported")
        print("• System checks every 1 minute for broadcasts to send")
        print("• Once sent, status changes to 'Sent' automatically")
        print()
        print("🎉 You're all set! Happy broadcasting!")
        print()

        # Add example recipient
        print("="*80)
        print("📝 ADDING EXAMPLE RECIPIENT")
        print("="*80)
        print()

        example_added = broadcast_manager.add_recipient(
            name="Example Customer",
            phone="60120000000",
            notes="Test recipient - you can delete this"
        )

        if example_added:
            print("✅ Added example recipient to 'Broadcast Recipients' sheet")
            print("   Name: Example Customer")
            print("   Phone: 60120000000")
            print("   You can delete this row and add your real customers")
        print()

        # Show stats
        stats = broadcast_manager.get_stats()
        print("="*80)
        print("📊 CURRENT STATS:")
        print("="*80)
        print(f"Total Broadcasts: {stats.get('total_broadcasts', 0)}")
        print(f"Pending: {stats.get('pending', 0)}")
        print(f"Sent: {stats.get('sent', 0)}")
        print(f"Total Messages Sent: {stats.get('total_messages_sent', 0)}")
        print()

    except FileNotFoundError:
        print(f"❌ Error: Credentials file not found: {credentials_file}")
        print("   Make sure you have the Google service account JSON file")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
