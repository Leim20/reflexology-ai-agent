"""
AI-Driven DateTime Parser
Converts user's date/time input to standardized format using AI.
No keyword matching - AI handles all languages naturally.
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any
import pytz

logger = logging.getLogger(__name__)

# Configuration
TIMEZONE = "Asia/Kuala_Lumpur"
OPENING_HOUR = 10  # 10:00 AM
CLOSING_HOUR = 24  # 12:00 AM (midnight)

DATETIME_PARSER_PROMPT = """You are a datetime normalizer for a massage booking system.

Context:
- Timezone: Asia/Kuala_Lumpur
- Opening hours: 10:00 - 24:00 (10am to midnight)
- Current date/time: {reference_now}

Task:
From the user's message, extract booking date and time.

Rules:
- Date format: YYYY-MM-DD (e.g., 2025-12-28)
- Time format: HH:MM in 24-hour format (e.g., 20:00 for 8pm)
- If date is relative (today, tomorrow, 今天, 明天, esok, hari ini), convert to actual YYYY-MM-DD
- If AM/PM is unclear (e.g., "8点" could be 8am or 8pm):
  - Prefer the interpretation within opening hours (10:00-24:00)
  - If still ambiguous, set ambiguous=true and provide followup_question
- If time is outside opening hours, set needs_followup=true

Output ONLY valid JSON (no explanation, no markdown):
{{
  "date": "YYYY-MM-DD" or null,
  "time": "HH:MM" or null,
  "confidence": 0.0 to 1.0,
  "ambiguous": true/false,
  "needs_followup": true/false,
  "followup_question": "question in user's language" or null
}}"""


def get_reference_now() -> str:
    """Get current datetime in configured timezone"""
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M (%A)")


def ai_parse_datetime(user_message: str, openai_client) -> Dict[str, Any]:
    """
    Parse user's date/time input using AI.

    Args:
        user_message: The user's message containing date/time info
        openai_client: OpenAI client instance

    Returns:
        Dict with: date, time, confidence, ambiguous, needs_followup, followup_question
    """
    logger.info("=" * 60)
    logger.info("AI DATETIME PARSER")
    logger.info(f"   Input: {user_message}")
    logger.info("=" * 60)

    reference_now = get_reference_now()

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # Fast and cheap for simple parsing
            messages=[
                {
                    "role": "system",
                    "content": DATETIME_PARSER_PROMPT.format(reference_now=reference_now)
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ],
            temperature=0,  # Deterministic output
            max_tokens=200
        )

        result_text = response.choices[0].message.content.strip()
        logger.info(f"   AI Response: {result_text}")

        # Parse JSON - handle potential markdown code blocks
        if result_text.startswith("```"):
            result_text = result_text.split("```")[1]
            if result_text.startswith("json"):
                result_text = result_text[4:]

        result = json.loads(result_text)

        # Add timezone info
        result["timezone"] = TIMEZONE

        logger.info(f"   Parsed: date={result.get('date')}, time={result.get('time')}")
        logger.info(f"   Confidence: {result.get('confidence')}, Ambiguous: {result.get('ambiguous')}")

        return result

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        return {
            "date": None,
            "time": None,
            "confidence": 0,
            "ambiguous": True,
            "needs_followup": True,
            "followup_question": "Please tell me the date and time you want to book?"
        }
    except Exception as e:
        logger.error(f"DateTime parser error: {e}")
        return {
            "date": None,
            "time": None,
            "confidence": 0,
            "ambiguous": True,
            "needs_followup": True,
            "followup_question": "Please tell me the date and time you want to book?"
        }


def is_valid_date(date_str: str) -> bool:
    """Validate date format YYYY-MM-DD"""
    if not date_str:
        return False
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def is_valid_time(time_str: str) -> bool:
    """Validate time format HH:MM"""
    if not time_str:
        return False
    try:
        datetime.strptime(time_str, "%H:%M")
        return True
    except ValueError:
        return False


def is_within_opening_hours(time_str: str) -> bool:
    """Check if time is within opening hours (10:00-24:00)"""
    if not time_str:
        return False
    try:
        time_obj = datetime.strptime(time_str, "%H:%M")
        hour = time_obj.hour
        return OPENING_HOUR <= hour < CLOSING_HOUR
    except ValueError:
        return False


def validate_datetime_result(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the parsed datetime result.
    Returns validation status and any issues.
    """
    issues = []

    if result.get("needs_followup"):
        return {
            "valid": False,
            "needs_followup": True,
            "followup_question": result.get("followup_question")
        }

    if not result.get("date"):
        issues.append("missing_date")
    elif not is_valid_date(result["date"]):
        issues.append("invalid_date_format")

    if not result.get("time"):
        issues.append("missing_time")
    elif not is_valid_time(result["time"]):
        issues.append("invalid_time_format")
    elif not is_within_opening_hours(result["time"]):
        issues.append("outside_opening_hours")

    if result.get("ambiguous"):
        issues.append("ambiguous")

    return {
        "valid": len(issues) == 0,
        "issues": issues,
        "needs_followup": len(issues) > 0,
        "followup_question": result.get("followup_question") if issues else None
    }
