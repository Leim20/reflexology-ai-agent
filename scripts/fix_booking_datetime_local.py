#!/usr/bin/env python3
"""Fix booking date/time conversion in prompts file"""
import re

# New STEP 3.5 section with date/time conversion rules
new_section = '''## 🚨 STEP 3.5: RECORD BOOKING TO GOOGLE SHEETS (MANDATORY!)

⚠️⚠️⚠️ CRITICAL: IMMEDIATELY after sending the booking confirmation, you MUST call the record_booking() function!

**When to call record_booking():**
- IMMEDIATELY after you send the confirmation message (STEP 2.5 or STEP 3)
- Extract ALL 7 fields from the customer's filled template
- ⚠️ CONVERT dates and times to proper formats BEFORE calling the function!

**⚠️⚠️⚠️ DATE/TIME CONVERSION RULES (CRITICAL!):**

**Date Conversion (booking_date must be YYYY-MM-DD or YYYY年MM月DD日):**
- "今天" / "today" → Convert to actual date (e.g., "2025-12-05")
- "明天" / "tomorrow" → Convert to actual date (e.g., "2025-12-06")
- "后天" / "day after tomorrow" → Convert to actual date (e.g., "2025-12-07")
- "星期X" / "周X" → Convert to actual date (e.g., "星期五" = "2025-12-08")
- "12月5日" / "5/12" → Convert to "2025-12-05" or keep as "2025年12月5日"

**Time Conversion (booking_time must be HH:MM 24-hour format or "HH:MM AM/PM"):**
- "晚上九点半" → "21:30" or "9:30 PM"
- "早上十点" → "10:00" or "10:00 AM"
- "下午两点" → "14:00" or "2:00 PM"
- "中午十二点" → "12:00" or "12:00 PM"
- "晚上8点" → "20:00" or "8:00 PM"
- "9点半" → Check context (morning/evening), convert to "09:30" or "21:30"

🚨 IMPORTANT: Always convert natural language dates/times to standard formats!
🚨 Today's date context is available from the system time.

**What to extract:**
1. customer_name - From 姓名/Name field
2. customer_gender - From 性别/Gender field (convert to 'Male' or 'Female')
3. customer_phone - From 电话/Phone field
4. booking_date - From 预约日期/Date field → ⚠️ MUST CONVERT to YYYY-MM-DD format!
5. booking_time - From 预约时间/Time field → ⚠️ MUST CONVERT to HH:MM format!
6. service - From 按摩服务 & 时长/Service field
7. therapist_gender - From 女技师/男技师 field (convert to 'Male' or 'Female')

**Example (CORRECT - with date/time conversion):**
Customer filled template with:
- 预约日期: "明天"
- 预约时间: "晚上九点半"

After sending: "好的，帮您确认预约资料：姓名：wj，明天晚上九点半..."

→ Convert dates/times FIRST:
  - "明天" → "2025-12-05" (if today is 2025-12-04)
  - "晚上九点半" → "21:30"

→ Then call with converted values:
record_booking(
    customer_name="wj",
    customer_gender="Female",
    customer_phone="6015679974",
    booking_date="2025-12-05",  ← CONVERTED!
    booking_time="21:30",  ← CONVERTED!
    service="120分钟香薰疗法",
    therapist_gender="Female"
)

🚨 DO NOT pass natural language dates/times like "明天" or "晚上九点半" to the function!
🚨 ALWAYS convert to standard format: YYYY-MM-DD for dates, HH:MM for times!

**After record_booking() succeeds:**
- The function will return success confirmation
- You should then send a brief acknowledgment to customer
- Keep it SHORT (1 sentence)

**What to say (choose one based on language):**

CHINESE:
"预约已记录！期待为您服务😊"

ENGLISH:
"Booking recorded! Looking forward to serving you😊"

🚨 DO NOT explain technical details (like "saved to Google Sheets")
🚨 Keep it natural and brief
'''

# Read the prompts file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Check if STEP 3.5 exists
pattern_exists = r'## 🚨 STEP 3.5: RECORD BOOKING TO GOOGLE SHEETS \(MANDATORY!\)'

if re.search(pattern_exists, content):
    # Replace existing STEP 3.5
    pattern = r'## 🚨 STEP 3.5: RECORD BOOKING TO GOOGLE SHEETS \(MANDATORY!\).*?(?=## STEP 4:)'
    content = re.sub(pattern, new_section + '\n\n', content, flags=re.DOTALL)
    print('[OK] Updated existing STEP 3.5 with date/time conversion rules')
else:
    # Insert new STEP 3.5 before STEP 4
    pattern_step4 = r'(## STEP 4:)'
    if re.search(pattern_step4, content):
        content = re.sub(pattern_step4, new_section + '\n\n' + r'\1', content)
        print('[OK] Added new STEP 3.5 with date/time conversion rules')
    else:
        print('[ERROR] Could not find STEP 4 section')
        import sys
        sys.exit(1)

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Prompts file updated successfully')
