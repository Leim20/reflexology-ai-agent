"""
Extraction Optimizer
Combines multiple AI extraction calls into one and reduces frequency
Token savings: ~60% reduction in extraction API calls
"""

from typing import Dict, Any, Optional, List
from datetime import datetime
import json
from utils.logger import get_logger

logger = get_logger(__name__)


class ExtractionOptimizer:
    """
    Optimizes AI extraction calls by:
    1. Batching multiple extractions into single API call
    2. Only running extraction at milestones (not every message)
    3. Using gpt-4o-mini for cost efficiency
    """

    # Extraction runs at these milestones (message counts)
    EXTRACTION_MILESTONES = [5, 10, 15, 20]

    # Also extract when these keywords detected (booking completed, goodbye)
    EXTRACTION_TRIGGERS = [
        'done', 'confirmed', 'booked', 'thank', 'bye', 'see you',
        '预约', '确认', '谢谢', '再见', '拜拜', '好的'
    ]

    def __init__(self):
        self.last_extraction: Dict[str, datetime] = {}  # session_id -> timestamp
        self.extraction_cache: Dict[str, Dict] = {}  # session_id -> cached result
        self.min_extraction_interval = 120  # seconds between extractions

    def should_extract(self, session_id: str, message_count: int,
                       last_user_message: str = "") -> bool:
        """
        Determine if extraction should run based on milestones and triggers

        Args:
            session_id: Session identifier
            message_count: Current number of messages in conversation
            last_user_message: The last message from user (for trigger detection)

        Returns:
            bool: True if extraction should run
        """
        # Check milestone
        is_milestone = message_count in self.EXTRACTION_MILESTONES

        # Check trigger words
        has_trigger = any(
            trigger.lower() in last_user_message.lower()
            for trigger in self.EXTRACTION_TRIGGERS
        )

        # Check time since last extraction
        last_time = self.last_extraction.get(session_id)
        time_ok = True
        if last_time:
            elapsed = (datetime.now() - last_time).total_seconds()
            time_ok = elapsed >= self.min_extraction_interval

        should_run = (is_milestone or has_trigger) and time_ok

        if should_run:
            logger.debug(f"Extraction triggered: milestone={is_milestone}, trigger={has_trigger}")
        else:
            logger.debug(f"Extraction skipped: milestone={is_milestone}, trigger={has_trigger}, time_ok={time_ok}")

        return should_run

    def extract_all(self, messages: List[Dict], customer_phone: str,
                    ai_engine, session_id: str) -> Dict[str, Any]:
        """
        Combined extraction - gets interest, preferences, and summary in ONE API call
        Uses gpt-4o-mini for cost efficiency

        Args:
            messages: Conversation messages
            customer_phone: Customer's phone number
            ai_engine: AIEngine instance
            session_id: Session identifier for caching

        Returns:
            dict: {
                'interest': str,
                'preferences': str,
                'summary': str,
                'success': bool
            }
        """
        logger.info("="*60)
        logger.info("🔍 COMBINED EXTRACTION (Optimized)")
        logger.info("="*60)

        try:
            # Extract customer messages only
            customer_messages = []
            for msg in messages[-15:]:  # Last 15 messages
                if msg.get('role') == 'user':
                    content = msg.get('content', '')
                    if isinstance(content, str) and content.strip():
                        customer_messages.append(content[:150])

            if not customer_messages:
                logger.info("No customer messages to analyze")
                return {
                    'interest': 'Initial contact',
                    'preferences': '',
                    'summary': 'New conversation',
                    'success': True
                }

            customer_text = "\n".join([f"- {msg}" for msg in customer_messages])

            # Combined extraction prompt
            extraction_prompt = f"""Analyze this customer conversation and extract information.

Customer messages:
{customer_text}

Return a JSON object with these fields:
{{
    "interest": "What service/topic interested them (e.g., 'Body massage 90min', 'Membership inquiry', 'Foot massage booking')",
    "preferences": "Any preferences mentioned (e.g., 'Female therapist, evening time, cupping add-on')",
    "summary": "Brief 10-word summary of what customer wanted"
}}

Only include information actually mentioned. Use empty string if not mentioned.
Return ONLY the JSON object, no other text."""

            # Use gpt-4o-mini for cost efficiency
            response = ai_engine.generate_response(
                [{"role": "user", "content": extraction_prompt}],
                model="gpt-4o-mini",  # Cheaper model for extraction
                temperature=0.2,
                max_tokens=200
            )

            if response.get('success') and response.get('content'):
                content = response['content'].strip()

                # Parse JSON response
                try:
                    # Clean up response if needed
                    if content.startswith('```'):
                        content = content.split('```')[1]
                        if content.startswith('json'):
                            content = content[4:]

                    result = json.loads(content)
                    result['success'] = True

                    # Update cache and timestamp
                    self.extraction_cache[session_id] = result
                    self.last_extraction[session_id] = datetime.now()

                    logger.info(f"✅ Extraction complete:")
                    logger.info(f"   Interest: {result.get('interest', 'N/A')}")
                    logger.info(f"   Preferences: {result.get('preferences', 'N/A')}")
                    logger.info(f"   Summary: {result.get('summary', 'N/A')}")
                    logger.info("="*60)

                    return result

                except json.JSONDecodeError as e:
                    logger.warning(f"JSON parse error: {e}, using raw content")
                    # Fallback - extract what we can
                    return {
                        'interest': content[:100] if content else 'Unknown',
                        'preferences': '',
                        'summary': content[:50] if content else 'Conversation',
                        'success': True
                    }
            else:
                logger.warning("Extraction API call failed")
                return {
                    'interest': 'Initial contact',
                    'preferences': '',
                    'summary': 'Conversation',
                    'success': False
                }

        except Exception as e:
            logger.error(f"Extraction error: {e}")
            return {
                'interest': 'Initial contact',
                'preferences': '',
                'summary': 'Conversation',
                'success': False
            }

    def get_cached_extraction(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get cached extraction result if available"""
        return self.extraction_cache.get(session_id)

    def clear_cache(self, session_id: str) -> None:
        """Clear cache for a session"""
        self.extraction_cache.pop(session_id, None)
        self.last_extraction.pop(session_id, None)


# Global instance
extraction_optimizer = ExtractionOptimizer()
