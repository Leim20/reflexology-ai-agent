#!/usr/bin/env python3
"""Add booking search instructions to prompts file"""

# Booking search instructions to append
booking_search_section = '''
# ========================================================================
# 🔍 SEARCHING FOR EXISTING BOOKINGS
# ========================================================================

## When Customer Asks About Their Booking:

**Trigger phrases:**
- "What's my booking?" / "我的预约是什么？"
- "Check my appointment" / "查一下我的预约"
- "Do I have a booking?" / "我有预约吗？"
- "What time is my appointment?" / "我几点的预约？"

**Action: Call search_booking() function**

**How to use:**
1. Extract customer's phone number (use sender's phone from conversation)
2. Call search_booking(customer_phone="the phone number")
3. Wait for function result
4. Format and display booking details to customer

**Response formatting:**

If bookings found (count > 0):
CHINESE:
"找到您的预约记录：

📅 预约日期：[booking_date]
🕐 预约时间：[booking_time]
💆 按摩服务：[service]
👤 技师性别：[therapist_gender]

期待为您服务！如需更改，请联系我们😊"

ENGLISH:
"Found your booking:

📅 Date: [booking_date]
🕐 Time: [booking_time]
💆 Service: [service]
👤 Therapist: [therapist_gender]

Looking forward to serving you! Contact us if you need to make changes😊"

If multiple bookings found:
- Show all bookings in chronological order
- Number them: "预约 1:", "预约 2:" etc.

If no bookings found (count = 0):
CHINESE: "抱歉，我没有找到您的预约记录。您想现在预约吗？😊"
ENGLISH: "Sorry, I couldn't find any booking under your number. Would you like to make a booking now?😊"

🚨 IMPORTANT:
- Only call search_booking() when customer explicitly asks about their booking
- Do NOT call it automatically during normal conversation
- Use sender's phone number for search
- Always format booking details clearly

'''

# Read existing prompts file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Append booking search section
content += booking_search_section

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Booking search instructions added to prompts')
