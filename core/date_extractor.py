"""
Date and Time Extractor for Malaysian Multilingual Environment

Hybrid approach:
1. Python dictionary normalization (free, fast)
2. dateparser library for parsing (free, accurate)
3. GPT-4o-mini fallback for edge cases (small cost, handles slang/typos)

Supports: English, Chinese (Simplified/Traditional), Malay, Mixed languages
"""

import re
import os
import dateparser
from dotenv import load_dotenv
load_dotenv()
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
import pytz
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)

# Malaysia timezone
MALAYSIA_TZ = pytz.timezone('Asia/Kuala_Lumpur')

# ============================================================
# NORMALIZATION DICTIONARY
# Converts Chinese/Malay date expressions to English
# ============================================================

NORMALIZE_TO_ENGLISH = {
    # ============ RELATIVE DAYS ============
    # Note: Adding trailing space to prevent "tomorrowmorning" issue
    # Chinese
    '今天': 'today ',
    '今日': 'today ',
    '明天': 'tomorrow ',
    '明日': 'tomorrow ',
    '后天': 'day after tomorrow ',
    '後天': 'day after tomorrow ',
    '大后天': 'in 3 days ',
    '大後天': 'in 3 days ',

    # Malay
    'hari ini': 'today ',
    'esok': 'tomorrow ',
    'lusa': 'day after tomorrow ',
    'tulat': 'in 3 days ',

    # ============ NEXT/THIS MODIFIERS ============
    # Note: dateparser doesn't handle "next Monday" well
    # So we use empty string for "下个" - PREFER_DATES_FROM: 'future' will pick next occurrence
    # For "下下个" we add "in 1 week" after the weekday
    # Chinese (longer patterns first)
    '下下下个': 'in 2 weeks ',     # 3 weeks from now
    '下下下個': 'in 2 weeks ',
    '下下个': 'in 1 week ',        # 2 weeks from now
    '下下個': 'in 1 week ',
    '下个': '',                     # next occurrence (PREFER_DATES_FROM handles it)
    '下個': '',
    '这个': '',                     # this week
    '這個': '',
    '这周': '',                     # this week
    '下周': 'in 1 week ',           # next week
    '下下周': 'in 2 weeks ',        # week after next

    # Malay
    'minggu depan': 'in 1 week ',
    'minggu hadapan': 'in 1 week ',
    'minggu ini': '',
    'depan': '',                    # Remove "next" prefix

    # English (dateparser doesn't handle "next Monday" well)
    'next next next ': 'in 2 weeks ',  # Rare but handle it
    'next next ': 'in 1 week ',
    'next ': '',                       # Just remove "next", PREFER_DATES_FROM handles it

    # ============ WEEKDAYS - FULL FORMS ============
    # Note: Adding trailing space to prevent "Tuesdayafternoon" issue
    # 星期X
    '星期一': 'Monday ',
    '星期二': 'Tuesday ',
    '星期三': 'Wednesday ',
    '星期四': 'Thursday ',
    '星期五': 'Friday ',
    '星期六': 'Saturday ',
    '星期日': 'Sunday ',
    '星期天': 'Sunday ',

    # 礼拜X / 禮拜X
    '礼拜一': 'Monday ',
    '礼拜二': 'Tuesday ',
    '礼拜三': 'Wednesday ',
    '礼拜四': 'Thursday ',
    '礼拜五': 'Friday ',
    '礼拜六': 'Saturday ',
    '礼拜日': 'Sunday ',
    '礼拜天': 'Sunday ',
    '禮拜一': 'Monday ',
    '禮拜二': 'Tuesday ',
    '禮拜三': 'Wednesday ',
    '禮拜四': 'Thursday ',
    '禮拜五': 'Friday ',
    '禮拜六': 'Saturday ',
    '禮拜日': 'Sunday ',
    '禮拜天': 'Sunday ',

    # 周X / 週X
    '周一': 'Monday ',
    '周二': 'Tuesday ',
    '周三': 'Wednesday ',
    '周四': 'Thursday ',
    '周五': 'Friday ',
    '周六': 'Saturday ',
    '周日': 'Sunday ',
    '週一': 'Monday ',
    '週二': 'Tuesday ',
    '週三': 'Wednesday ',
    '週四': 'Thursday ',
    '週五': 'Friday ',
    '週六': 'Saturday ',
    '週日': 'Sunday ',

    # ============ WEEKDAYS - SHORT FORMS ============
    # 拜X (Malaysian Chinese style)
    '拜一': 'Monday ',
    '拜二': 'Tuesday ',
    '拜三': 'Wednesday ',
    '拜四': 'Thursday ',
    '拜五': 'Friday ',
    '拜六': 'Saturday ',
    '拜日': 'Sunday ',
    '拜天': 'Sunday ',

    # Number variations
    '星期1': 'Monday ',
    '星期2': 'Tuesday ',
    '星期3': 'Wednesday ',
    '星期4': 'Thursday ',
    '星期5': 'Friday ',
    '星期6': 'Saturday ',
    '星期7': 'Sunday ',
    '礼拜1': 'Monday ',
    '礼拜2': 'Tuesday ',
    '礼拜3': 'Wednesday ',
    '礼拜4': 'Thursday ',
    '礼拜5': 'Friday ',
    '礼拜6': 'Saturday ',
    '礼拜7': 'Sunday ',
    '拜1': 'Monday ',
    '拜2': 'Tuesday ',
    '拜3': 'Wednesday ',
    '拜4': 'Thursday ',
    '拜5': 'Friday ',
    '拜6': 'Saturday ',
    '拜7': 'Sunday ',

    # Malay weekdays
    'isnin': 'Monday ',
    'selasa': 'Tuesday ',
    'rabu': 'Wednesday ',
    'khamis': 'Thursday ',
    'jumaat': 'Friday ',
    'sabtu': 'Saturday ',
    'ahad': 'Sunday ',

    # ============ MONTHS ============
    # Chinese
    '一月': 'January',
    '二月': 'February',
    '三月': 'March',
    '四月': 'April',
    '五月': 'May',
    '六月': 'June',
    '七月': 'July',
    '八月': 'August',
    '九月': 'September',
    '十月': 'October',
    '十一月': 'November',
    '十二月': 'December',

    # ============ TIME PERIODS ============
    # Chinese
    '凌晨': 'early morning ',
    '早上': 'morning ',
    '上午': 'morning ',
    '中午': 'noon ',
    '下午': 'afternoon ',
    '傍晚': 'evening ',
    '晚上': 'evening ',
    '半夜': 'midnight ',

    # Malay
    'pagi': 'morning ',
    'tengahari': 'noon ',
    'petang': 'afternoon ',
    'malam': 'evening ',

    # ============ TIME EXPRESSIONS ============
    # Chinese time
    '点半': ':30 ',
    '點半': ':30 ',
    '点钟': ':00 ',
    '點鐘': ':00 ',
    '点': ':00 ',
    '點': ':00 ',
    '半': ':30 ',

    # Malay time
    'pukul': '',
    'setengah': ':30 ',

    # ============ DATE SUFFIXES ============
    '号': ' ',
    '號': ' ',
    '日': ' ',
}

# Time normalization patterns (Chinese numbers to digits)
CHINESE_NUMBERS = {
    '零': '0', '一': '1', '二': '2', '三': '3', '四': '4',
    '五': '5', '六': '6', '七': '7', '八': '8', '九': '9',
    '十': '10', '十一': '11', '十二': '12',
    '两': '2', '兩': '2',
}


def _normalize_chinese_numbers(text: str) -> str:
    """Convert Chinese numbers to digits for time (e.g., 三点 -> 3点)"""
    result = text

    # Handle special cases like 十一, 十二 first
    for cn, digit in sorted(CHINESE_NUMBERS.items(), key=lambda x: len(x[0]), reverse=True):
        result = result.replace(cn, digit)

    return result


def _normalize_to_english(text: str) -> str:
    """
    Normalize Chinese/Malay text to English using dictionary.
    Fast and free - no API calls.
    """
    result = text

    # First convert Chinese numbers
    result = _normalize_chinese_numbers(result)

    # Sort by length (longer patterns first to avoid partial matches)
    sorted_mappings = sorted(
        NORMALIZE_TO_ENGLISH.items(),
        key=lambda x: len(x[0]),
        reverse=True
    )

    for original, english in sorted_mappings:
        result = result.replace(original, english)
        # Also try lowercase
        result = result.replace(original.lower(), english)

    # Post-processing: Convert "afternoon 3:00" to "3pm", "morning 10:00" to "10am"
    # This is needed because dateparser handles "3pm" better than "afternoon 3:00"
    result = _convert_time_format(result)

    return result


def _convert_time_format(text: str) -> str:
    """
    Convert time expressions to dateparser-friendly format.
    Examples:
    - "afternoon 3:00" -> "3pm"
    - "morning 10:30" -> "10:30am"
    - "evening 8:00" -> "8pm"
    """
    import re

    # Detect time period and determine am/pm
    # IMPORTANT: Sorted by length (longest first) to prevent "noon" matching before "afternoon"
    period_mapping = [
        ('early morning', 'am'),
        ('afternoon', 'pm'),
        ('midnight', 'am'),
        ('morning', 'am'),
        ('evening', 'pm'),
        ('noon', 'pm'),
    ]

    # Find if any time period is in the text
    suffix = ''
    for period, ampm in period_mapping:
        if period in text.lower():
            suffix = ampm
            # Remove the period word
            text = re.sub(rf'\s*{period}\s*', ' ', text, flags=re.IGNORECASE)
            break

    # Convert :00 and :30 time formats to 12-hour with am/pm
    # Pattern: number followed by :00 or :30
    def replace_time(match):
        hour = match.group(1)
        minutes = match.group(2) if match.group(2) else '00'
        # Use detected suffix, or default to empty (dateparser will figure it out)
        time_suffix = suffix
        if minutes == '00':
            return f'{hour}{time_suffix}'
        else:
            return f'{hour}:{minutes}{time_suffix}'

    # Match patterns like "3:00 " or "10:30 "
    text = re.sub(r'(\d{1,2}):(\d{2})\s*', replace_time, text)

    # Clean up multiple spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def _handle_relative_weekday(text: str, base_date: datetime) -> str:
    """
    Handle patterns like "in 1 week Wednesday" that dateparser can't parse.
    Converts to absolute date format.

    Examples:
    - "in 1 week Wednesday" -> "2026-02-19" (Wednesday next week)
    - "in 2 weeks Monday" -> "2026-02-23" (Monday in 2 weeks)
    """
    import re

    # Pattern: "in X week(s) [weekday]" or "[weekday] in X week(s)"
    weekdays = {
        'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
        'friday': 4, 'saturday': 5, 'sunday': 6
    }

    # Try both patterns
    patterns = [
        r'in\s+(\d+)\s+weeks?\s+(\w+)',  # "in 1 week Wednesday"
        r'(\w+)\s+in\s+(\d+)\s+weeks?',  # "Wednesday in 1 week"
    ]

    for i, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if i == 0:  # "in X week(s) [weekday]"
                weeks = int(match.group(1))
                weekday_str = match.group(2).lower()
            else:  # "[weekday] in X week(s)"
                weekday_str = match.group(1).lower()
                weeks = int(match.group(2))

            if weekday_str in weekdays:
                target_weekday = weekdays[weekday_str]
                current_weekday = base_date.weekday()

                # Calculate days to next occurrence of target weekday
                days_ahead = target_weekday - current_weekday
                if days_ahead <= 0:  # Target day is today or already passed this week
                    days_ahead += 7

                # Add the weeks offset
                total_days = days_ahead + (weeks * 7)
                target_date = base_date + timedelta(days=total_days)

                # Replace the pattern with the absolute date
                date_str = target_date.strftime('%Y-%m-%d')
                text = re.sub(pattern, date_str, text, flags=re.IGNORECASE)
                logger.info(f"   Converted relative weekday: {match.group(0)} -> {date_str}")

    return text


def _normalize_with_llm(text: str) -> str:
    """
    Fallback: Use GPT-4o-mini to normalize when dictionary fails.
    Costs ~$0.0001 per call.
    """
    try:
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": """You are a date/time extractor for a Malaysian booking system.

Extract the date and time from the user message and convert to English.

Rules:
1. Output ONLY the date/time expression in English
2. If no date/time found, output exactly: NONE
3. Handle Chinese, Malay, English, and mixed languages
4. Convert relative dates (tomorrow, next week) and specific dates (2月15号, 15 Feb)
5. Convert times to 12-hour format with am/pm

Examples:
- "我要book拜3下午" -> "Wednesday afternoon"
- "下下个礼拜2 3点" -> "next next Tuesday 3pm"
- "esok pagi 10点" -> "tomorrow morning 10am"
- "nxt sat 2pm" -> "next Saturday 2pm"
- "2月15号 下午3点半" -> "February 15 3:30pm"
- "你好吗" -> "NONE"
- "有什么服务" -> "NONE"

Output ONLY the English date/time or NONE. No explanation."""
                },
                {
                    "role": "user",
                    "content": text
                }
            ],
            temperature=0,
            max_tokens=50
        )

        result = response.choices[0].message.content.strip()
        logger.info(f"   LLM normalized: '{text}' -> '{result}'")
        return result

    except Exception as e:
        logger.error(f"LLM normalization failed: {e}")
        return "NONE"


def extract_datetime(user_message: str) -> Dict[str, Optional[str]]:
    """
    Extract date and time from user message.

    Hybrid approach:
    1. Try dictionary normalization + dateparser (free)
    2. Fallback to LLM normalization if dictionary fails

    Args:
        user_message: User's message in any language

    Returns:
        {
            'date': 'YYYY-MM-DD' or None,
            'time': 'HH:MM' or None,
            'method': 'dictionary' | 'llm' | 'none',
            'normalized': the normalized text used
        }
    """
    now = datetime.now(MALAYSIA_TZ)

    logger.info(f"DATE EXTRACTION: '{user_message[:50]}...'" if len(user_message) > 50 else f"DATE EXTRACTION: '{user_message}'")

    # ========================================
    # STEP 1: Dictionary Normalization
    # ========================================
    dict_normalized = _normalize_to_english(user_message)
    logger.info(f"   Dictionary normalized: '{dict_normalized[:80]}...'" if len(dict_normalized) > 80 else f"   Dictionary normalized: '{dict_normalized}'")

    # ========================================
    # STEP 1.5: Handle "in X week(s) [weekday]" patterns
    # ========================================
    dict_normalized = _handle_relative_weekday(dict_normalized, now)

    # ========================================
    # STEP 2: Try dateparser with dictionary result
    # ========================================
    result = dateparser.parse(
        dict_normalized,
        settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': now,
            'RETURN_AS_TIMEZONE_AWARE': False,
        },
        languages=['en', 'zh']
    )

    if result:
        extracted_date = result.date().strftime('%Y-%m-%d')
        extracted_time = result.strftime('%H:%M') if result.hour != 0 or result.minute != 0 else None

        # Don't return time if it's exactly 00:00 (likely no time was specified)
        if extracted_time == '00:00':
            extracted_time = None

        logger.info(f"   Dictionary SUCCESS: date={extracted_date}, time={extracted_time}")

        return {
            'date': extracted_date,
            'time': extracted_time,
            'method': 'dictionary',
            'normalized': dict_normalized
        }

    # ========================================
    # STEP 3: Fallback to LLM
    # ========================================
    logger.info(f"   Dictionary failed, trying LLM fallback...")

    llm_normalized = _normalize_with_llm(user_message)

    if llm_normalized == "NONE" or not llm_normalized:
        logger.info(f"   No date/time found in message")
        return {
            'date': None,
            'time': None,
            'method': 'none',
            'normalized': None
        }

    # ========================================
    # STEP 3.5: Re-apply dictionary normalization to LLM result
    # ========================================
    llm_normalized = _normalize_to_english(llm_normalized)
    llm_normalized = _handle_relative_weekday(llm_normalized, now)
    logger.info(f"   LLM result after dict normalization: '{llm_normalized}'")

    # ========================================
    # STEP 4: Try dateparser with LLM result
    # ========================================
    result = dateparser.parse(
        llm_normalized,
        settings={
            'PREFER_DATES_FROM': 'future',
            'RELATIVE_BASE': now,
            'RETURN_AS_TIMEZONE_AWARE': False,
        },
        languages=['en']
    )

    if result:
        extracted_date = result.date().strftime('%Y-%m-%d')
        extracted_time = result.strftime('%H:%M') if result.hour != 0 or result.minute != 0 else None

        if extracted_time == '00:00':
            extracted_time = None

        logger.info(f"   LLM SUCCESS: date={extracted_date}, time={extracted_time}")

        return {
            'date': extracted_date,
            'time': extracted_time,
            'method': 'llm',
            'normalized': llm_normalized
        }

    logger.info(f"   Both dictionary and LLM failed to extract date/time")
    return {
        'date': None,
        'time': None,
        'method': 'none',
        'normalized': llm_normalized
    }


def extract_date_only(user_message: str) -> Optional[str]:
    """Convenience function to extract only date."""
    result = extract_datetime(user_message)
    return result.get('date')


def extract_time_only(user_message: str) -> Optional[str]:
    """Convenience function to extract only time."""
    result = extract_datetime(user_message)
    return result.get('time')
