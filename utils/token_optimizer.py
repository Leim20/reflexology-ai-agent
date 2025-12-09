"""
Token Optimizer
Provides utilities for restructuring messages to maximize OpenAI prompt caching
and reduce token consumption.

OpenAI Prompt Caching:
- Caches prompt prefixes that remain constant across requests
- Gives 50% discount on cached tokens
- Requires static content at the START of messages

Token Savings Strategy:
1. Static content first (system prompt, knowledge base) - CACHED
2. Dynamic content last (memory, context) - NOT cached but small
"""

from typing import List, Dict, Any, Optional
from utils.logger import get_logger

logger = get_logger(__name__)


class TokenOptimizer:
    """
    Optimizes token usage through:
    1. Message restructuring for prompt caching
    2. Knowledge base section extraction
    3. Memory context compression
    """

    # Keywords for selective KB section retrieval
    KB_SECTION_KEYWORDS = {
        'pricing': ['price', 'cost', 'rm', 'how much', '多少钱', '价格', 'fee'],
        'cupping': ['cupping', '拔罐', 'cup'],
        'guasha': ['guasha', 'gua sha', '刮痧', 'scraping'],
        'booking': ['book', 'appointment', '预约', '预订', 'reserve'],
        'membership': ['member', '会员', 'register', '注册', 'birthday', '生日'],
        'hours': ['hour', 'time', 'open', 'close', '几点', '营业', '时间'],
        'therapist': ['therapist', 'male', 'female', '技师', '男', '女'],
    }

    def __init__(self):
        self.cached_static_content = None
        self.kb_sections = {}

    def structure_messages_for_caching(
        self,
        system_prompt: str,
        knowledge_base: str,
        memory_context: Optional[str],
        conversation: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Structure messages to maximize OpenAI prompt caching.

        Order (for caching):
        1. System prompt (STATIC - cached)
        2. Knowledge base (STATIC - cached)
        3. Memory context (DYNAMIC - not cached, but small)
        4. Conversation history

        Args:
            system_prompt: The system prompt text
            knowledge_base: Full or filtered knowledge base
            memory_context: Optional customer memory/context
            conversation: List of conversation messages

        Returns:
            List of properly structured messages
        """
        messages = []

        # 1. System prompt (STATIC - will be cached)
        messages.append({
            "role": "system",
            "content": system_prompt
        })

        # 2. Knowledge base as separate system message (STATIC - will be cached)
        # This allows the KB to be cached even if conversation varies
        if knowledge_base:
            messages.append({
                "role": "system",
                "content": f"REFERENCE INFORMATION:\n{knowledge_base}"
            })

        # 3. Memory context (DYNAMIC - small, not cached)
        if memory_context:
            messages.append({
                "role": "system",
                "content": memory_context
            })

        # 4. Conversation history
        for msg in conversation:
            # Skip system messages from conversation (already added above)
            if msg.get('role') != 'system':
                messages.append({
                    "role": msg.get('role'),
                    "content": msg.get('content')
                })

        logger.debug(f"Structured {len(messages)} messages for caching")
        return messages

    def get_relevant_kb_sections(
        self,
        full_kb: str,
        user_message: str,
        always_include: List[str] = None
    ) -> str:
        """
        Extract only relevant KB sections based on user message.
        Reduces KB tokens by ~50-70% for most queries.

        Args:
            full_kb: The full knowledge base text
            user_message: The user's message to analyze
            always_include: Sections to always include (e.g., ['BUSINESS_INFO'])

        Returns:
            Filtered knowledge base with relevant sections only
        """
        if not full_kb:
            return ""

        always_include = always_include or ['BUSINESS_INFO']
        user_message_lower = user_message.lower()

        # Determine which sections are relevant
        relevant_sections = set(always_include)

        for section, keywords in self.KB_SECTION_KEYWORDS.items():
            if any(kw in user_message_lower for kw in keywords):
                relevant_sections.add(section.upper())

        # If no specific keywords matched, include pricing (most common)
        if len(relevant_sections) == len(always_include):
            relevant_sections.add('SERVICES_PRICING')

        # Parse and filter KB sections
        sections = self._parse_kb_sections(full_kb)
        filtered_parts = []

        for section_name, section_content in sections.items():
            section_upper = section_name.upper()
            if any(rs in section_upper for rs in relevant_sections):
                filtered_parts.append(section_content)

        result = "\n\n".join(filtered_parts)
        reduction = (1 - len(result) / len(full_kb)) * 100 if full_kb else 0

        logger.debug(f"KB filtered: {len(full_kb)} -> {len(result)} chars ({reduction:.0f}% reduction)")

        return result if result else full_kb[:2000]  # Fallback to first 2000 chars

    def _parse_kb_sections(self, kb_text: str) -> Dict[str, str]:
        """Parse KB into sections by header markers"""
        if not kb_text:
            return {}

        sections = {}
        current_section = "INTRO"
        current_content = []

        for line in kb_text.split('\n'):
            # Check if this is a section header
            if line.strip().endswith(':') and line.strip().isupper():
                # Save previous section
                if current_content:
                    sections[current_section] = '\n'.join(current_content)
                # Start new section
                current_section = line.strip().rstrip(':')
                current_content = [line]
            elif '# =' in line and '=' * 10 in line:
                # Skip separator lines but don't start new section
                continue
            else:
                current_content.append(line)

        # Save last section
        if current_content:
            sections[current_section] = '\n'.join(current_content)

        return sections

    def compress_memory_context(
        self,
        memory_data: Dict[str, Any],
        max_tokens: int = 200
    ) -> str:
        """
        Compress memory context to essential information only.

        Args:
            memory_data: Customer memory dictionary
            max_tokens: Maximum tokens for memory context

        Returns:
            Compressed memory string
        """
        if not memory_data:
            return ""

        # Extract only essential fields
        essential = []

        name = memory_data.get('name')
        if name and name != 'Unknown':
            essential.append(f"Name: {name}")

        # Last preference (most recent only)
        prefs = memory_data.get('preferences', '')
        if prefs and prefs != 'None':
            # Take only first 100 chars of preferences
            essential.append(f"Preferences: {prefs[:100]}")

        # Conversation count
        count = memory_data.get('total_conversations', 0)
        if count > 1:
            essential.append(f"Returning customer ({count} visits)")

        # Member status
        if memory_data.get('is_member'):
            essential.append("Member: Yes")

        if not essential:
            return ""

        result = "CUSTOMER CONTEXT:\n" + "\n".join(essential)

        # Truncate if too long (rough estimate: 1 token ≈ 4 chars)
        max_chars = max_tokens * 4
        if len(result) > max_chars:
            result = result[:max_chars] + "..."

        return result


# Global instance
token_optimizer = TokenOptimizer()


def estimate_tokens(text: str) -> int:
    """Quick token estimation (1 token ≈ 4 characters)"""
    return len(text) // 4 if text else 0


def log_token_usage(
    system_prompt: str,
    knowledge_base: str,
    memory: str,
    conversation: List[Dict],
    label: str = "Message"
) -> Dict[str, int]:
    """Log estimated token usage for debugging"""
    tokens = {
        'system_prompt': estimate_tokens(system_prompt),
        'knowledge_base': estimate_tokens(knowledge_base),
        'memory': estimate_tokens(memory),
        'conversation': sum(
            estimate_tokens(str(m.get('content', '')))
            for m in conversation
        ),
    }
    tokens['total'] = sum(tokens.values())

    logger.info(f"📊 Token Estimate ({label}):")
    logger.info(f"   System prompt: {tokens['system_prompt']}")
    logger.info(f"   Knowledge base: {tokens['knowledge_base']}")
    logger.info(f"   Memory: {tokens['memory']}")
    logger.info(f"   Conversation: {tokens['conversation']}")
    logger.info(f"   TOTAL: {tokens['total']}")

    return tokens
