#!/usr/bin/env python3
"""Add booking search functions to app.py"""
import re

# Read the file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\web\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Functions to add
new_functions = '''

def get_search_booking_function_definition():
    """Define search_booking function for OpenAI function calling"""
    return {
        "type": "function",
        "function": {
            "name": "search_booking",
            "description": "Search for existing bookings by customer phone number. Use this when customer asks about their booking, wants to check booking details, or asks 'what is my booking?'",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number to search for bookings. Use the sender's phone number if customer asks about 'my booking'."
                    }
                },
                "required": ["customer_phone"]
            }
        }
    }


def handle_search_booking_function_call(function_args: dict) -> dict:
    """Handle search_booking function call from AI"""
    logger.info("="*80)
    logger.info("🔍 HANDLING BOOKING SEARCH FUNCTION CALL")
    logger.info("="*80)

    customer_phone = function_args.get('customer_phone', '')

    logger.info(f"📞 Searching for phone: {customer_phone}")

    if not customer_phone:
        logger.error("❌ Missing customer phone number")
        return {'success': False, 'bookings': [], 'count': 0, 'message': 'Phone number is required'}

    try:
        if not lead_manager:
            return {'success': False, 'bookings': [], 'count': 0, 'message': 'Booking system not available'}

        result = lead_manager.get_bookings(customer_phone=customer_phone)

        if result['success']:
            count = result['count']
            logger.info(f"✅ Found {count} booking(s)")
            return result
        else:
            return result

    except Exception as e:
        logger.error(f"❌ Exception: {str(e)}")
        return {'success': False, 'bookings': [], 'count': 0, 'message': f'Error: {str(e)}'}
'''

# Find handle_record_booking_function_call and insert after it
pattern = r'(def handle_record_booking_function_call.*?return \{[^}]+\})'
match = re.search(pattern, content, re.DOTALL)

if match:
    # Find the end of handle_record_booking_function_call
    end_pos = match.end()
    content = content[:end_pos] + new_functions + content[end_pos:]
    print('[OK] Step 1: Booking search functions added to app.py')
else:
    print('[ERROR] Could not find handle_record_booking_function_call')
    import sys
    sys.exit(1)

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\web\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Booking search functions added successfully')
