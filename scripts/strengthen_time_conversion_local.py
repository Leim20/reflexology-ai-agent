#!/usr/bin/env python3
"""Strengthen time conversion instructions"""
import re

# Strengthened conversion rules
new_conversion_rules = '''**⚠️⚠️⚠️ DATE/TIME CONVERSION RULES (CRITICAL!):**

🚨 YOU MUST CONVERT BOTH DATE **AND** TIME TO STANDARD FORMATS!
🚨 DO NOT convert only the date and forget the time!

**Date Conversion (booking_date must be YYYY-MM-DD or YYYY年MM月DD日):**
- "今天" / "today" → Convert to actual date (e.g., "2025-12-05")
- "明天" / "tomorrow" → Convert to actual date (e.g., "2025-12-06")
- "后天" / "day after tomorrow" → Convert to actual date (e.g., "2025-12-07")
- "星期X" / "周X" → Convert to actual date (e.g., "星期五" = "2025-12-08")
- "12月5日" / "5/12" → Convert to "2025-12-05" or keep as "2025年12月5日"

**Time Conversion (booking_time must be HH:MM 24-hour format):**
- "晚上九点半" → "21:30"
- "下午五点半" → "17:30"
- "下午两点" → "14:00"
- "早上十点" → "10:00"
- "中午十二点" → "12:00"
- "晚上8点" → "20:00"
- "傍晚六点" → "18:00"
- "上午九点半" → "09:30"
- "凌晨一点" → "01:00"

**Time Keywords to Recognize:**
- 早上/上午/早晨 = Morning (06:00-11:59) → Use 24-hour format as-is
- 中午 = Noon (12:00) → "12:00"
- 下午 = Afternoon (12:00-17:59) → Add 12 to hour if needed
- 傍晚/晚上 = Evening/Night (18:00-23:59) → Use 18+ hours
- 凌晨/深夜 = Late night/Early morning (00:00-05:59) → Use 00-05 hours
- "点" = o'clock
- "点半" = :30
- "点一刻" = :15
- "点三刻" = :45

🚨 CONVERSION STEPS (DO BOTH!):
1. Convert DATE first: "明天" → "2025-12-06"
2. Convert TIME next: "下午五点半" → "17:30"
3. Then call record_booking() with BOTH converted values!

🚨 IMPORTANT: Always convert natural language dates/times to standard formats!
🚨 Today's date context is available from the system time.
'''

# New example section with both cases
new_example = '''**Example 1 (Night time - 晚上九点半):**
Customer filled template with:
- 预约日期: "明天"
- 预约时间: "晚上九点半"

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

**Example 2 (Afternoon time - 下午五点半):**
Customer filled template with:
- 预约日期: "明天"
- 预约时间: "下午五点半"

→ Convert dates/times FIRST:
  - "明天" → "2025-12-06" (if today is 2025-12-05)
  - "下午五点半" → "17:30" (下午 = afternoon, 五点半 = 5:30, so 17:30)

→ Then call with converted values:
record_booking(
    customer_name="wjj",
    customer_gender="Female",
    customer_phone="60987654321",
    booking_date="2025-12-06",  ← CONVERTED!
    booking_time="17:30",  ← CONVERTED!
    service="120分钟身体按摩",
    therapist_gender="Female"
)

🚨 DO NOT pass natural language dates/times like "明天" or "下午五点半" to the function!
🚨 ALWAYS convert to standard format: YYYY-MM-DD for dates, HH:MM for times!'''

# Read the prompts file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Step 1: Replace DATE/TIME CONVERSION RULES section
pattern1 = r'\*\*⚠️⚠️⚠️ DATE/TIME CONVERSION RULES \(CRITICAL!\):\*\*.*?(?=\*\*What to extract:\*\*)'
if re.search(pattern1, content, re.DOTALL):
    content = re.sub(pattern1, new_conversion_rules + '\n\n', content, flags=re.DOTALL)
    print('[OK] Step 1: Strengthened DATE/TIME conversion rules')
else:
    print('[ERROR] Could not find DATE/TIME CONVERSION RULES section')

# Step 2: Replace example section
pattern2 = r'\*\*Example.*?with date/time conversion\):\*\*.*?🚨 ALWAYS convert to standard format: YYYY-MM-DD for dates, HH:MM for times!'
if re.search(pattern2, content, re.DOTALL):
    content = re.sub(pattern2, new_example, content, flags=re.DOTALL)
    print('[OK] Step 2: Added afternoon time example')
else:
    print('[WARNING] Could not find example section to replace')

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Local prompts file updated successfully')
