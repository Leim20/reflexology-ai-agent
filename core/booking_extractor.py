"""Booking Field Extractor - LLM structured output extraction for booking fields"""
import json
from typing import Optional
from utils.logger import get_logger

logger = get_logger(__name__)

BOOKING_KEYWORDS = [
    "book", "booking", "appointment", "reserve", "schedule",
    "预约", "预订", "订", "tempah",
    "tomorrow", "today", "monday", "tuesday", "wednesday",
    "thursday", "friday", "saturday", "sunday",
    "am", "pm", "morning", "afternoon", "evening",
    "massage", "reflexology", "body", "foot", "head",
    "male", "female", "therapist",
    "男", "女", "技师", "师傅",
    "按摩", "足部", "全身",
]

EXTRACTION_PROMPT = """You are a booking field extractor for a reflexology center.

Extract ONLY the booking details the customer EXPLICITLY stated in their message.
Do NOT assume or infer anything not directly stated.
Do NOT use the customer's WhatsApp profile name - only use a name if they typed it themselves.

Return a JSON object with these fields (use null for anything NOT explicitly mentioned):

{{
  "customer_name": "string or null - ONLY if user typed their name in this message",
  "customer_gender": "string or null - 'Male' or 'Female' only if mentioned",
  "service": "string or null - e.g. 'foot reflexology', 'body massage', '90min body massage'",
  "date": "string or null - e.g. 'tomorrow', '2025-12-01', 'this Saturday'",
  "time": "string or null - e.g. '5pm', '17:00', 'afternoon'",
  "therapist_gender": "string or null - 'Male' or 'Female' only if mentioned",
  "phone": "string or null - ONLY if user typed a phone number"
}}

IMPORTANT RULES:
- Return ONLY the JSON object, no other text
- Use null for any field the customer did NOT explicitly state
- For customer_name: ONLY extract if the user literally wrote their name (e.g. "my name is Alex", "I'm Sarah", "名字是小明"). NEVER use WhatsApp profile name.
- For customer_gender: ONLY extract if they said their gender (e.g. "I'm male", "女", "我是男生")
- For service: ONLY extract if they mentioned a specific service type
- For therapist_gender: ONLY extract if they mentioned therapist preference (e.g. "female therapist", "女技师", "男师傅")
- For phone: Extract if they typed a phone number (e.g. "my number is 012-345-6789") OR if they indicate using their current number. IMPORTANT: If they say "this number", "this one", "用这个号码", "这个号码", "same number", return the EXACT string "this number" (not null).

Customer message: {message}"""


def has_booking_intent(message: str) -> bool:
    """Check if the message contains booking-related keywords."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in BOOKING_KEYWORDS)


def extract_booking_fields(message: str, ai_engine, phone_fallback: Optional[str] = None) -> dict:
    """
    Use LLM structured output to extract booking fields from a user message.

    Args:
        message: The user's raw message text
        ai_engine: AIEngine instance for making LLM calls
        phone_fallback: WhatsApp phone number to use if user says "this number"

    Returns:
        dict with extracted fields (None for unmentioned fields)
    """
    prompt = EXTRACTION_PROMPT.format(message=message)

    try:
        response = ai_engine.generate_response(
            [{"role": "user", "content": prompt}],
            temperature=0.0,
            max_tokens=300,
            model="gpt-4o-mini",
        )

        if not response.get("success"):
            logger.error("Booking extraction LLM call failed: %s", response.get("error"))
            return {}

        content = response["content"].strip()

        # Strip markdown code fences if present
        if content.startswith("```"):
            content = content.split("\n", 1)[-1]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        extracted = json.loads(content)

        # Handle "this number" pattern - expand to catch more variations
        phone_val = (extracted.get("phone") or "").lower().strip()
        this_number_patterns = [
            "this number", "this one", "same number", "current number",
            "用这个号码", "这个号码", "这个电话", "用这个", "同一个号码"
        ]
        if any(p in phone_val for p in this_number_patterns) and phone_fallback:
            extracted["phone"] = phone_fallback

        # Remove null values so merge only overwrites with real data
        cleaned = {k: v for k, v in extracted.items() if v is not None}

        logger.info("BOOKING EXTRACTION | fields=%s", list(cleaned.keys()))
        return cleaned

    except json.JSONDecodeError as e:
        logger.error("Booking extraction JSON parse failed: %s | raw=%s", e, content[:200] if 'content' in dir() else 'N/A')
        return {}
    except Exception as e:
        logger.error("Booking extraction error: %s", e)
        return {}
