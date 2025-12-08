#!/usr/bin/env python3
"""Add booking integration to app.py"""

import re
import sys

# Read the file
import os
script_dir = os.path.dirname(os.path.abspath(__file__))
app_path = os.path.join(script_dir, '..', 'web', 'app.py')
with open(app_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add booking tool function definitions before handle_escalation_function_call
booking_functions = '''

def get_record_booking_function_definition():
    """Define record_booking function for OpenAI function calling"""
    return {
        "type": "function",
        "function": {
            "name": "record_booking",
            "description": "Record a confirmed booking to the Bookings sheet when customer has filled in the booking template and you have sent the confirmation. ONLY call this function AFTER you send the booking confirmation message with all details. Extract the booking information from the customer's filled template.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Customer's name from the booking template (姓名/Name field)"
                    },
                    "customer_gender": {
                        "type": "string",
                        "description": "Customer's gender from booking template (性别/Gender field). Must be 'Male' or 'Female'. Recognize: 男/男生/Male/M/boy/man = 'Male', 女/女生/Female/F/girl/woman = 'Female'"
                    },
                    "customer_phone": {
                        "type": "string",
                        "description": "Customer's phone number from booking template (电话/Phone field). Extract digits only."
                    },
                    "booking_date": {
                        "type": "string",
                        "description": "Date of appointment from booking template (预约日期/Date field) in YYYY-MM-DD format or original format provided"
                    },
                    "booking_time": {
                        "type": "string",
                        "description": "Time of appointment from booking template (预约时间/Time field) as provided by customer"
                    },
                    "service": {
                        "type": "string",
                        "description": "Service type and duration from booking template (按摩服务 & 时长 field). Example: '90分钟足部按摩', '120min body massage'"
                    },
                    "therapist_gender": {
                        "type": "string",
                        "description": "Therapist gender preference from booking template (女技师/男技师 field). Must be 'Male' or 'Female'. Recognize: 男技师/Male therapist/男师傅 = 'Male', 女技师/Female therapist/女师傅 = 'Female'"
                    }
                },
                "required": ["customer_name", "customer_gender", "customer_phone", "booking_date", "booking_time", "service", "therapist_gender"]
            }
        }
    }


def handle_record_booking_function_call(function_args: dict) -> dict:
    """Handle record_booking function call from AI"""
    logger.info("="*80)
    logger.info("📅 HANDLING BOOKING RECORDING FUNCTION CALL")
    logger.info("="*80)

    customer_name = function_args.get('customer_name', '')
    customer_gender = function_args.get('customer_gender', '')
    customer_phone = function_args.get('customer_phone', '')
    booking_date = function_args.get('booking_date', '')
    booking_time = function_args.get('booking_time', '')
    service = function_args.get('service', '')
    therapist_gender = function_args.get('therapist_gender', '')

    logger.info(f"📋 Booking Details:")
    logger.info(f"   Name: {customer_name}")
    logger.info(f"   Gender: {customer_gender}")
    logger.info(f"   Phone: {customer_phone}")
    logger.info(f"   Date: {booking_date}")
    logger.info(f"   Time: {booking_time}")
    logger.info(f"   Service: {service}")
    logger.info(f"   Therapist: {therapist_gender}")

    if not all([customer_name, customer_gender, customer_phone, booking_date, booking_time, service, therapist_gender]):
        logger.error("❌ Missing required booking information")
        return {'success': False, 'message': 'Missing required booking information'}

    try:
        if not lead_manager:
            return {'success': False, 'message': 'Booking system not available'}

        result = lead_manager.record_booking(
            customer_name=customer_name,
            customer_gender=customer_gender,
            customer_phone=customer_phone,
            booking_date=booking_date,
            booking_time=booking_time,
            service=service,
            therapist_gender=therapist_gender
        )

        if result['success']:
            logger.info(f"✅ Booking recorded: Row {result['row']}")
            return {'success': True, 'message': f"Booking recorded in row {result['row']}"}
        else:
            return {'success': False, 'message': result['message']}

    except Exception as e:
        logger.error(f"❌ Exception: {str(e)}")
        return {'success': False, 'message': f'Error: {str(e)}'}
'''

# Find and insert before handle_escalation_function_call
pattern = r'(def handle_escalation_function_call\()'
if re.search(pattern, content):
    content = re.sub(pattern, booking_functions + '\n\n\\1', content)
    print('[OK] Step 1: Booking tool functions added')
else:
    print('[ERROR] Could not find handle_escalation_function_call')
    sys.exit(1)

# 2. Add booking tool to tools array
pattern = r'(get_register_member_function_definition\(\))\n(\s+\])'
replacement = r'\1,\n            get_record_booking_function_definition()\n\2'
if re.search(pattern, content):
    content = re.sub(pattern, replacement, content)
    print('[OK] Step 2: Booking tool added to tools array')
else:
    print('[ERROR] Could not update tools array')
    sys.exit(1)

# 3. Add booking handling in tool_calls processing
pattern = r'(elif function_name == "register_member":.*?function_results\.append\({[^}]+}\))'
match = re.search(pattern, content, re.DOTALL)
if match:
    register_member_block = match.group(1)
    booking_handler = '''

                elif function_name == "record_booking":
                    booking_result = handle_record_booking_function_call(
                        function_args=function_args
                    )

                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(booking_result)
                    })'''

    content = content.replace(register_member_block, register_member_block + booking_handler)
    print('[OK] Step 3: Booking handler added to tool_calls processing')
else:
    print('[ERROR] Could not add booking handler')
    sys.exit(1)

# Write back
with open(app_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('\n[OK] All booking integration added successfully!')
