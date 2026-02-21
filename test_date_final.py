"""Final date extraction test"""
from core.date_extractor import extract_datetime
from datetime import datetime
import pytz

tests = [
    "下个星期二下午3点",      # Next Tuesday 3pm
    "明天早上10点",           # Tomorrow morning 10am
    "esok pagi 9am",          # Tomorrow morning 9am (Malay)
    "下下个礼拜三",           # Next next Wednesday
    "拜五下午2点半",          # Friday 2:30pm (Malaysian Chinese)
    "next Monday 2pm",        # English
    "next next Tuesday 10am", # English (2 weeks from now)
]

print("=== Date Extraction Test ===")
now = datetime.now(pytz.timezone('Asia/Kuala_Lumpur'))
print(f"Current date/time: {now.strftime('%Y-%m-%d %H:%M %A')}")
print()

for test in tests:
    result = extract_datetime(test)
    print(f"Input: {test}")
    print(f"  Date: {result['date']}")
    print(f"  Time: {result['time']}")
    print(f"  Method: {result['method']}")
    print()
