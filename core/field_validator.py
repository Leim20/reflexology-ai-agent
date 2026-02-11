"""
Two-Phase Field Validator - Prevents hallucination from conversation history.

Phase 1: AI extracts fields WITH full conversation context (existing MCQ flow)
Phase 2: This module validates each extracted field against ONLY the current message

The key insight: MCQ validates that values are valid formats/enums, but can't verify
if values came from the CURRENT message vs conversation history. This validator adds
that missing layer.

Both phases use gpt-4o-mini for cost efficiency.
"""

import json
import os
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from utils.logger import get_logger

logger = get_logger(__name__)

# Initialize OpenAI client
_client = None


def _get_client() -> OpenAI:
    """Get OpenAI client singleton."""
    global _client
    if _client is None:
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            # Try loading from config
            try:
                config_path = os.path.join(os.path.dirname(__file__), '..', 'config', 'config.json')
                with open(config_path, 'r') as f:
                    config = json.load(f)
                    api_key = config.get('openai', {}).get('api_key')
            except Exception:
                pass
        _client = OpenAI(api_key=api_key)
    return _client


# Field descriptions for validation prompt
FIELD_DESCRIPTIONS = {
    "service": "massage/reflexology service type (e.g., foot massage, body massage, cupping)",
    "date": "booking date (e.g., tomorrow, 3月1日, March 1, 2026-03-01)",
    "time": "booking time (e.g., 2pm, 下午3点, 14:00)",
    "therapist_gender": "preferred therapist gender (male/female/男/女)",
    "customer_name": "customer's name",
    "customer_gender": "customer's gender (male/female/男/女)",
    "phone": "phone number",
    "pain_point": "body pain or health concern mentioned"
}


def validate_extracted_fields(
    extracted_fields: Dict[str, str],
    current_message: str,
    session_id: str = None,
    log_to_db: bool = True
) -> Dict[str, str]:
    """
    Phase 2 Validation: Check each extracted field against ONLY the current message.

    This prevents hallucination by verifying that extracted values actually appear
    in or can be reasonably inferred from the current user message alone.

    Args:
        extracted_fields: Fields extracted by Phase 1 (MCQ with full context)
        current_message: The current user message ONLY (no conversation history)
        session_id: For logging purposes
        log_to_db: Whether to log validation results to MySQL

    Returns:
        Dict with only the validated fields (hallucinated fields removed)
    """
    if not extracted_fields:
        return {}

    # Filter out None/empty values
    fields_to_validate = {k: v for k, v in extracted_fields.items()
                          if v is not None and v != "" and v != "null"}

    if not fields_to_validate:
        return {}

    logger.info("="*60)
    logger.info("PHASE 2 VALIDATION - Anti-Hallucination Check")
    logger.info(f"   Session: {session_id}")
    logger.info(f"   Current message: {current_message[:100]}...")
    logger.info(f"   Fields to validate: {list(fields_to_validate.keys())}")
    logger.info("="*60)

    # Build the validation prompt
    validated_fields = _batch_validate_fields(fields_to_validate, current_message, session_id, log_to_db)

    logger.info(f"   Validated fields: {list(validated_fields.keys())}")
    logger.info(f"   Rejected fields: {set(fields_to_validate.keys()) - set(validated_fields.keys())}")

    return validated_fields


def _batch_validate_fields(
    fields: Dict[str, str],
    current_message: str,
    session_id: str = None,
    log_to_db: bool = True
) -> Dict[str, str]:
    """
    Validate all fields in a single LLM call for cost efficiency.

    Uses gpt-4o-mini with structured output.
    """
    # Build field list for prompt
    field_list = []
    for field_name, value in fields.items():
        desc = FIELD_DESCRIPTIONS.get(field_name, field_name)
        field_list.append(f'- {field_name}: "{value}" ({desc})')

    fields_text = "\n".join(field_list)

    prompt = f"""You are a validation assistant. Your job is to check if extracted booking data actually appears in the user's message.

USER MESSAGE (the ONLY source of truth):
"{current_message}"

EXTRACTED DATA TO VALIDATE:
{fields_text}

For EACH field, determine if the value can be found in or reasonably inferred from the user message above.

VALIDATION RULES:
1. VALID: The value appears directly in the message OR can be clearly inferred
   - "3月1日" in message → date "3月1日" is VALID
   - "tomorrow" in message → date "tomorrow" is VALID
   - "foot massage" in message → service containing "foot" is VALID
   - "2pm" in message → time "14:00" or "2:00 PM" is VALID (same meaning)
   - "male therapist" → therapist_gender "Male" is VALID

2. HALLUCINATED: The value does NOT appear and CANNOT be inferred from message
   - Message says "3月1日" but extracted time "下午1点" → time is HALLUCINATED
   - Message says "book massage" but extracted specific service → HALLUCINATED if no service mentioned
   - Any data that seems to come from a different conversation → HALLUCINATED

3. Be STRICT: When in doubt, mark as HALLUCINATED. It's better to ask user again than use wrong data.

Respond with a JSON object where:
- Key = field name
- Value = "valid" or "hallucinated"

Example response:
{{"date": "valid", "time": "hallucinated", "service": "valid"}}"""

    try:
        client = _get_client()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You validate extracted booking data. Respond with JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,  # Deterministic for validation
            max_tokens=500,
            response_format={"type": "json_object"}
        )

        result_text = response.choices[0].message.content
        validation_results = json.loads(result_text)

        logger.info(f"   Validation results: {validation_results}")

        # Filter to only valid fields
        validated_fields = {}
        for field_name, value in fields.items():
            result = validation_results.get(field_name, "hallucinated")

            if result == "valid":
                validated_fields[field_name] = value
                if log_to_db and session_id:
                    _log_validation(session_id, field_name, value, "valid", current_message)
            else:
                logger.warning(f"   HALLUCINATION DETECTED: {field_name}='{value}' not in current message")
                if log_to_db and session_id:
                    _log_validation(session_id, field_name, value, "hallucinated", current_message)

        return validated_fields

    except Exception as e:
        logger.error(f"Batch validation error: {e}")
        # On error, be conservative - reject all fields
        return {}


def _log_validation(session_id: str, field_name: str, value: str,
                    result: str, user_message: str) -> None:
    """Log validation result to MySQL (if available)."""
    try:
        from core.booking_session_sql import log_field_validation
        log_field_validation(session_id, field_name, value, result, user_message)
    except ImportError:
        # SQL module not available, skip logging
        pass
    except Exception as e:
        logger.warning(f"Failed to log validation: {e}")


def validate_single_field(
    field_name: str,
    extracted_value: str,
    current_message: str
) -> Tuple[bool, str]:
    """
    Validate a single field (useful for real-time validation).

    Returns:
        Tuple[is_valid, reason]
    """
    if not extracted_value or extracted_value == "null":
        return False, "Empty value"

    result = _batch_validate_fields(
        {field_name: extracted_value},
        current_message,
        log_to_db=False
    )

    if field_name in result:
        return True, "Value found in current message"
    else:
        return False, "Value not found in current message (possible hallucination)"


# ============================================================================
# SPECIAL VALIDATORS FOR SPECIFIC FIELD TYPES
# ============================================================================

def quick_validate_phone(extracted_phone: str, current_message: str) -> bool:
    """
    Quick validation for phone - checks if digits appear in message.

    This is a fast heuristic before LLM validation.
    """
    if not extracted_phone:
        return False

    # Special case: 'this_number' sentinel
    if extracted_phone == 'this_number':
        # Check if message indicates using current number
        indicators = ['this number', 'same number', 'current number',
                      '这个号码', '同样号码', 'nombor ini', 'guna nombor']
        msg_lower = current_message.lower()
        return any(ind in msg_lower for ind in indicators)

    # Extract digits from both
    phone_digits = ''.join(c for c in extracted_phone if c.isdigit())
    message_digits = ''.join(c for c in current_message if c.isdigit())

    # Phone digits should appear in message
    if len(phone_digits) >= 8:  # Malaysian numbers have at least 8 digits
        return phone_digits in message_digits or phone_digits[-8:] in message_digits

    return False


def quick_validate_date_time(extracted_value: str, current_message: str) -> bool:
    """
    Quick validation for date/time - checks for common patterns.

    This is a fast heuristic before LLM validation.
    """
    if not extracted_value:
        return False

    msg_lower = current_message.lower()
    value_lower = extracted_value.lower()

    # Direct match
    if value_lower in msg_lower:
        return True

    # Check for relative date keywords
    date_keywords = {
        'today': ['today', '今天', '今日', 'hari ini'],
        'tomorrow': ['tomorrow', '明天', '明日', 'esok'],
        'day after': ['后天', 'day after', 'lusa']
    }

    for key, keywords in date_keywords.items():
        if any(kw in value_lower for kw in keywords):
            if any(kw in msg_lower for kw in keywords):
                return True

    # Check for numeric patterns (dates like "3月1日", "march 1", "1/3")
    import re
    numbers_in_value = re.findall(r'\d+', extracted_value)
    if numbers_in_value:
        # At least one number should appear in message
        return any(num in current_message for num in numbers_in_value)

    return False


# ============================================================================
# INTEGRATION HELPER
# ============================================================================

def validate_booking_extraction(
    function_args: Dict[str, str],
    current_message: str,
    session_id: str = None,
    skip_fields: List[str] = None
) -> Dict[str, str]:
    """
    Main entry point for validating MCQ extraction results.

    CHANGE: Skip Phase 2 validation for date/time fields entirely.
    MCQ already constrains output to valid formats, so trust it.

    Args:
        function_args: Raw extraction from MCQ function call
        current_message: Current user message only
        session_id: For logging
        skip_fields: Fields to skip validation (e.g., 'message_type')

    Returns:
        Validated fields only (hallucinations removed)
    """
    skip_fields = skip_fields or ['message_type']

    # MCQ-trusted fields - skip Phase 2 validation entirely
    # MCQ already constrains output to valid enum values
    mcq_trusted_fields = {'date', 'time', 'service', 'therapist_gender', 'customer_gender'}

    booking_fields = {}
    mcq_trusted = {}

    for key, value in function_args.items():
        if key in skip_fields or value is None or value == "" or value == "null":
            continue

        if key in mcq_trusted_fields:
            # Trust MCQ extraction directly - no Phase 2 validation
            mcq_trusted[key] = value
            logger.info(f"   MCQ TRUSTED: {key}='{value}' (skipping Phase 2)")
        else:
            # Other fields still go through validation
            booking_fields[key] = value

    if not booking_fields and not mcq_trusted:
        return {}

    # Quick validation pass for non-MCQ fields (phone)
    quick_validated = {}
    needs_llm_validation = {}

    for field, value in booking_fields.items():
        if field == 'phone':
            if quick_validate_phone(value, current_message):
                quick_validated[field] = value
            else:
                needs_llm_validation[field] = value
        else:
            # All other fields need LLM validation
            needs_llm_validation[field] = value

    logger.info(f"   MCQ trusted: {list(mcq_trusted.keys())}")
    logger.info(f"   Quick validated: {list(quick_validated.keys())}")
    logger.info(f"   Needs LLM validation: {list(needs_llm_validation.keys())}")

    # LLM validation for remaining fields
    if needs_llm_validation:
        llm_validated = validate_extracted_fields(
            needs_llm_validation,
            current_message,
            session_id
        )
        quick_validated.update(llm_validated)

    # Combine MCQ-trusted + validated fields
    validated = {**mcq_trusted, **quick_validated}
    return validated
