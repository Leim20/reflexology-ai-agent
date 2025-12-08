"""Date/Time Parser Utility for Booking System"""
import re
from datetime import datetime, timedelta
from typing import Dict, Any

def parse_booking_datetime(date_str: str, time_str: str) -> Dict[str, Any]:
    """
    Parse natural language date/time to formal format.

    Args:
        date_str: Date string (e.g., 'tomorrow', '2025-12-07', 'next Monday', '12/7')
        time_str: Time string (e.g., '3pm', '15:00', '3:30 PM', 'afternoon')

    Returns:
        dict: {
            'success': bool,
            'date': str (YYYY-MM-DD format),
            'time': str (HH:MM format),
            'original_date': str,
            'original_time': str
        }
    """
    result = {
        'success': False,
        'date': date_str,
        'time': time_str,
        'original_date': date_str,
        'original_time': time_str
    }

    today = datetime.now()
    parsed_date = None
    parsed_time = None

    # ===== DATE PARSING =====
    date_lower = date_str.lower().strip()

    # Already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        parsed_date = date_str

    # Today/tomorrow/day after tomorrow
    elif date_lower in ['today', '今天', '今日']:
        parsed_date = today.strftime('%Y-%m-%d')
    elif date_lower in ['tomorrow', '明天', '明日', 'tmr', 'tmrw']:
        parsed_date = (today + timedelta(days=1)).strftime('%Y-%m-%d')
    elif date_lower in ['day after tomorrow', '后天', '後天']:
        parsed_date = (today + timedelta(days=2)).strftime('%Y-%m-%d')

    # Next weekday (e.g., 'next Monday', 'this Friday')
    elif 'monday' in date_lower or '星期一' in date_lower or '周一' in date_lower:
        parsed_date = get_next_weekday(today, 0).strftime('%Y-%m-%d')
    elif 'tuesday' in date_lower or '星期二' in date_lower or '周二' in date_lower:
        parsed_date = get_next_weekday(today, 1).strftime('%Y-%m-%d')
    elif 'wednesday' in date_lower or '星期三' in date_lower or '周三' in date_lower:
        parsed_date = get_next_weekday(today, 2).strftime('%Y-%m-%d')
    elif 'thursday' in date_lower or '星期四' in date_lower or '周四' in date_lower:
        parsed_date = get_next_weekday(today, 3).strftime('%Y-%m-%d')
    elif 'friday' in date_lower or '星期五' in date_lower or '周五' in date_lower:
        parsed_date = get_next_weekday(today, 4).strftime('%Y-%m-%d')
    elif 'saturday' in date_lower or '星期六' in date_lower or '周六' in date_lower:
        parsed_date = get_next_weekday(today, 5).strftime('%Y-%m-%d')
    elif 'sunday' in date_lower or '星期日' in date_lower or '星期天' in date_lower or '周日' in date_lower:
        parsed_date = get_next_weekday(today, 6).strftime('%Y-%m-%d')

    # DD/MM or MM/DD format (assume DD/MM for Malaysia)
    elif re.match(r'^(\d{1,2})[/\-\.](\d{1,2})$', date_str):
        match = re.match(r'^(\d{1,2})[/\-\.](\d{1,2})$', date_str)
        day, month = int(match.group(1)), int(match.group(2))
        # If day > 12, it's definitely DD/MM
        if day > 12:
            parsed_date = f'{today.year}-{month:02d}-{day:02d}'
        else:
            # Assume DD/MM for Malaysia
            parsed_date = f'{today.year}-{month:02d}-{day:02d}'

    # DD/MM/YYYY or similar
    elif re.match(r'^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})$', date_str):
        match = re.match(r'^(\d{1,2})[/\-\.](\d{1,2})[/\-\.](\d{2,4})$', date_str)
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
        if year < 100:
            year += 2000
        parsed_date = f'{year}-{month:02d}-{day:02d}'

    # ===== TIME PARSING =====
    time_lower = time_str.lower().strip()

    # Already in HH:MM format
    if re.match(r'^\d{1,2}:\d{2}$', time_str):
        hour, minute = map(int, time_str.split(':'))
        if hour < 24 and minute < 60:
            parsed_time = f'{hour:02d}:{minute:02d}'

    # 12-hour format with AM/PM (e.g., '3pm', '3:30pm', '3:30 PM')
    elif re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM|a\.m\.|p\.m\.)$', time_str):
        match = re.match(r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm|AM|PM|a\.m\.|p\.m\.)$', time_str)
        hour = int(match.group(1))
        minute = int(match.group(2)) if match.group(2) else 0
        period = match.group(3).lower().replace('.', '')

        if period == 'pm' and hour != 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        parsed_time = f'{hour:02d}:{minute:02d}'

    # Time periods
    elif time_lower in ['morning', '早上', '上午']:
        parsed_time = '10:00'
    elif time_lower in ['noon', 'midday', '中午']:
        parsed_time = '12:00'
    elif time_lower in ['afternoon', '下午']:
        parsed_time = '14:00'
    elif time_lower in ['evening', '晚上', '傍晚']:
        parsed_time = '19:00'

    # Just hour (e.g., '3', '15')
    elif re.match(r'^(\d{1,2})$', time_str):
        hour = int(time_str)
        if 1 <= hour <= 12:
            # Assume PM for business hours
            if hour < 10:
                hour += 12
        parsed_time = f'{hour:02d}:00'

    # Chinese time format (e.g., '下午3点', '晚上8点半')
    elif re.search(r'(\d{1,2})[点點时時]', time_str):
        match = re.search(r'(\d{1,2})[点點时時](?:(\d{2})|半)?', time_str)
        if match:
            hour = int(match.group(1))
            minute = 30 if '半' in time_str else (int(match.group(2)) if match.group(2) else 0)

            # Adjust for period
            if any(x in time_str for x in ['下午', '晚上', 'pm', 'PM']) and hour < 12:
                hour += 12
            elif any(x in time_str for x in ['上午', '早上', 'am', 'AM']) and hour == 12:
                hour = 0

            parsed_time = f'{hour:02d}:{minute:02d}'

    # Update result
    if parsed_date:
        result['date'] = parsed_date
    if parsed_time:
        result['time'] = parsed_time

    result['success'] = parsed_date is not None or parsed_time is not None

    return result


def get_next_weekday(from_date: datetime, weekday: int) -> datetime:
    """Get the next occurrence of a weekday (0=Monday, 6=Sunday)"""
    days_ahead = weekday - from_date.weekday()
    if days_ahead <= 0:  # Target day already happened this week
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)
