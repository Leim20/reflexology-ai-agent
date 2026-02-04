"""Booking Field Extractor - LLM structured output extraction for booking fields

DEPRECATED: extract_booking_fields is no longer called from app.py.
Booking field extraction is now handled by the update_booking_fields function call,
which lets the conversation AI resolve contextual references with full context.
This file is kept for reference only.
"""
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
  "customer_gender": "string or null - 'Male' or 'Female' ONLY if the customer explicitly states THEIR OWN gender (e.g. '我是男生', '我是女的', 'I am male')",
  "pain_point": "string or null - body part that hurts/is tired (e.g. 'shoulder', 'back', 'legs', '肩膀', '背部', '腰')",
  "service": "string or null - e.g. 'foot reflexology', 'body massage', '90min body massage', '足部60分钟', '香薰疗法'",
  "date": "string or null - e.g. 'tomorrow', '明天', '后天', 'this Saturday', '星期六'",
  "time": "string or null - e.g. '5pm', '17:00', 'afternoon', '下午3点', '晚上8点'",
  "therapist_gender": "string or null - 'Male' or 'Female' if the customer states a preference for therapist gender (e.g. '男的', '女的', '要男技师', 'female therapist', 'male')",
  "phone": "string or null - ONLY if user typed a phone number"
}}

IMPORTANT RULES:
- Return ONLY the JSON object, no other text
- Use null for any field the customer did NOT explicitly state
- For pain_point: Extract if they mention body parts that are sore/tired/uncomfortable (e.g. "肩膀酸", "背部很累", "shoulders hurt", "腰不舒服")
- For customer_name: ONLY extract if the user literally wrote their name (e.g. "my name is Alex", "I'm Sarah", "名字是小明"). NEVER use WhatsApp profile name.
- For customer_gender: ONLY extract if the customer explicitly states THEIR OWN gender with self-referencing words (e.g. '我是男生', '我是女的', 'I am male'). A bare '男的' or '女的' without '我' is NOT customer_gender.
- For service: ONLY extract if they mentioned a specific service type
- For therapist_gender: Extract if the customer mentions a gender preference for the therapist (e.g. '男的', '女的', '要男技师', '女师傅', 'male therapist'). When the customer says just '男的' or '女的' without self-referencing, this is more likely therapist_gender.
- For phone: Extract if they typed a phone number (e.g. "my number is 012-345-6789") OR if they indicate using their current number. IMPORTANT: If they say "this number", "this one", "用这个号码", "这个号码", "same number", return the EXACT string "this number" (not null).

Customer message: {message}"""


def has_booking_intent(message: str) -> bool:
    """Check if the message contains booking-related keywords."""
    msg_lower = message.lower()
    return any(kw in msg_lower for kw in BOOKING_KEYWORDS)


def extract_booking_fields(message: str, ai_engine, phone_fallback: Optional[str] = None, current_step: Optional[str] = None) -> dict:
    """
    Use LLM structured output to extract booking fields from a user message.

    Args:
        message: The user's raw message text
        ai_engine: AIEngine instance for making LLM calls
        phone_fallback: WhatsApp phone number to use if user says "this number"
        current_step: Current booking flow step for disambiguation context

    Returns:
        dict with extracted fields (None for unmentioned fields)
    """
    prompt = EXTRACTION_PROMPT.format(message=message)

    # Add step context for disambiguation
    if current_step:
        step_context_map = {
            "pain_point": "The bot is currently asking about the customer's PAIN POINT or body discomfort. If the user mentions any body part or discomfort, extract it as 'pain_point'.",
            "service": "The bot is currently asking about SERVICE selection. If the user mentions a massage type or service, extract it as 'service'.",
            "datetime": "The bot is currently asking about DATE and TIME. If the user mentions any date or time, extract as 'date' and/or 'time'.",
            "therapist_gender": "The bot is currently asking about THERAPIST GENDER preference. If the user says '男/男的/male' or '女/女的/female', extract it as 'therapist_gender', NOT 'customer_gender'.",
            "personal_info": "The bot is currently asking for the customer's NAME and PHONE number. Extract as 'customer_name' and/or 'phone'.",
        }
        context = step_context_map.get(current_step, "")
        if context:
            prompt += f"\n\nCONTEXT: {context}"

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
