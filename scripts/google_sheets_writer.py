
import os
import sys
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build

# --- Configuration ---
# The ID of your Google Sheet.
# You can find this in the URL of your sheet: https://docs.google.com/spreadsheets/d/YOUR_SPREADSHEET_ID/edit
SPREADSHEET_ID = 'YOUR_SPREADSHEET_ID' 

# The name of the sheet (tab) you want to write to.
SHEET_NAME = 'Sheet1' 

# Path to your service account JSON key file.
# IMPORTANT: Make sure this file is secure and not publicly accessible.
# We assume it's placed in the 'config' directory.
SERVICE_ACCOUNT_FILE = os.path.join(os.path.dirname(__file__), '..', 'config', 'google-credentials.json')

# --- End of Configuration ---

def get_google_sheets_service():
    """Authenticates with the Google Sheets API and returns the service object."""
    try:
        creds = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=['https://www.googleapis.com/auth/spreadsheets'])
        service = build('sheets', 'v4', credentials=creds)
        return service
    except FileNotFoundError:
        print(f"Error: The service account file was not found at {SERVICE_ACCOUNT_FILE}")
        sys.exit(1)
    except Exception as e:
        print(f"An error occurred during authentication: {e}")
        sys.exit(1)

def append_lead_to_sheet(service, name, phone, interest):
    """Appends a new lead as a row to the specified Google Sheet."""
    try:
        sheet = service.spreadsheets()
        # The data to append, in the order of your sheet's columns
        row_data = [[name, phone, interest]]
        
        result = sheet.values().append(
            spreadsheetId=SPREADSHEET_ID,
            range=f"{SHEET_NAME}!A1",  # Append after the last row with data
            valueInputOption='USER_ENTERED',
            insertDataOption='INSERT_ROWS',
            body={'values': row_data}
        ).execute()
        
        print(f"Successfully appended lead to sheet: {result.get('updates').get('updatedRange')}")
        return True
    except Exception as e:
        print(f"An error occurred while appending data to the sheet: {e}")
        return False

if __name__ == "__main__":
    # This script expects exactly three arguments from the command line: name, phone, and interest.
    if len(sys.argv) != 4:
        print("Usage: python scripts/google_sheets_writer.py "<Name>" "<Phone>" "<Interest>"")
        sys.exit(1)

    lead_name = sys.argv[1]
    lead_phone = sys.argv[2]
    lead_interest = sys.argv[3]

    print(f"Attempting to save lead: Name='{lead_name}', Phone='{lead_phone}', Interest='{lead_interest}'")
    
    sheets_service = get_google_sheets_service()
    if sheets_service:
        append_lead_to_sheet(sheets_service, lead_name, lead_phone, lead_interest)
