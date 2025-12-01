"""
Test script for /api/track-outbound endpoint
Simulates MacroDroid sending a notification when it sends a WhatsApp message
"""

import requests
import json

# Configuration
SERVER_URL = "http://localhost:5000"  # Change this to your server URL
ENDPOINT = "/api/track-outbound"

def test_track_outbound():
    """Test the track-outbound API endpoint"""

    print("="*80)
    print("Testing /api/track-outbound endpoint")
    print("="*80)

    # Test Case 1: Complete payload
    print("\n[Test 1] Complete payload with all fields")
    payload1 = {
        "phone": "+60123456789",
        "name": "John Doe",
        "call_time": "2025-11-14T10:30:00",
        "message": "Thank you for calling! We'll get back to you soon."
    }

    response1 = send_request(payload1)
    print_response(response1)

    # Test Case 2: Minimal payload (only phone)
    print("\n[Test 2] Minimal payload - only phone number")
    payload2 = {
        "phone": "+60987654321"
    }

    response2 = send_request(payload2)
    print_response(response2)

    # Test Case 3: Missing phone number (should fail)
    print("\n[Test 3] Missing phone number - should return error")
    payload3 = {
        "name": "Jane Doe",
        "message": "Hello"
    }

    response3 = send_request(payload3)
    print_response(response3)

    # Test Case 4: Duplicate phone (update existing)
    print("\n[Test 4] Duplicate phone - should update existing lead")
    payload4 = {
        "phone": "+60123456789",
        "name": "John Doe (Updated)",
        "call_time": "2025-11-14T15:00:00"
    }

    response4 = send_request(payload4)
    print_response(response4)

    print("\n" + "="*80)
    print("Testing complete!")
    print("="*80)


def send_request(payload):
    """Send POST request to the endpoint"""
    try:
        url = f"{SERVER_URL}{ENDPOINT}"
        headers = {"Content-Type": "application/json"}

        print(f"\nSending POST to: {url}")
        print(f"Payload: {json.dumps(payload, indent=2)}")

        response = requests.post(url, json=payload, headers=headers, timeout=10)
        return response

    except requests.exceptions.ConnectionError:
        print("❌ ERROR: Could not connect to server")
        print(f"   Make sure the server is running at {SERVER_URL}")
        return None
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return None


def print_response(response):
    """Print response details"""
    if not response:
        return

    print(f"\nStatus Code: {response.status_code}")

    try:
        response_json = response.json()
        print(f"Response: {json.dumps(response_json, indent=2)}")

        if response_json.get('success'):
            print("✅ SUCCESS")
        else:
            print("❌ FAILED")
    except:
        print(f"Response (raw): {response.text}")


if __name__ == "__main__":
    print("\n⚠️  IMPORTANT: Make sure your Flask server is running before testing!")
    print("   Run: python web/app.py")
    print()
    input("Press Enter to continue with tests...")

    test_track_outbound()
