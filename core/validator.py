"""
Response Validator
Validates AI responses against knowledge base to detect hallucinations
"""

import re
from typing import Dict, List, Any
from utils.logger import get_logger

logger = get_logger(__name__)


class ResponseValidator:
    """
    Validates AI responses against knowledge base

    Features:
    - Extract mentioned prices/products from response
    - Check against knowledge base
    - Calculate confidence score
    - Generate warnings for hallucinations
    """

    def __init__(self, knowledge_base: str = ""):
        """
        Initialize Response Validator

        Args:
            knowledge_base (str): Knowledge base content to validate against
        """
        logger.info("="*80)
        logger.info("INITIALIZING RESPONSE VALIDATOR")
        logger.info("="*80)

        self.knowledge_base = knowledge_base.lower() if knowledge_base else ""
        self.has_kb = bool(knowledge_base)

        logger.debug(f"Knowledge base provided: {self.has_kb}")
        if self.has_kb:
            logger.debug(f"Knowledge base size: {len(knowledge_base)} characters")
        else:
            logger.warning("No knowledge base provided - validation will be skipped")

        logger.info("✓ Response Validator initialized")
        logger.info("="*80)

    def validate(self, response_text: str) -> Dict[str, Any]:
        """
        Validate AI response against knowledge base

        Args:
            response_text (str): AI-generated response

        Returns:
            dict: {
                'is_valid': bool,
                'confidence': float (0-1),
                'warnings': List[str],
                'details': {
                    'mentioned_prices': List[str],
                    'mentioned_products': List[str],
                    'suspicious_items': List[str]
                }
            }
        """
        logger.info("="*60)
        logger.info("VALIDATING AI RESPONSE")
        logger.info("="*60)

        logger.debug(f"Response length: {len(response_text)} characters")
        logger.debug(f"Knowledge base available: {self.has_kb}")

        result = {
            'is_valid': True,
            'confidence': 1.0,
            'warnings': [],
            'details': {
                'mentioned_prices': [],
                'mentioned_products': [],
                'suspicious_items': []
            }
        }

        # Skip validation if no knowledge base
        if not self.has_kb:
            logger.warning("⚠️ No knowledge base - skipping validation")
            result['confidence'] = 0.5
            result['warnings'].append("No knowledge base loaded - cannot validate response")
            return result

        response_lower = response_text.lower()
        logger.debug("Starting validation checks...")

        # 1. Extract and validate prices
        logger.debug("Checking prices...")
        price_pattern = r'rm\s*(\d+(?:\.\d{2})?)'
        response_prices = re.findall(price_pattern, response_lower)
        kb_prices = re.findall(price_pattern, self.knowledge_base)

        logger.debug(f"Found {len(response_prices)} prices in response")
        logger.debug(f"Found {len(kb_prices)} prices in knowledge base")

        for price in response_prices:
            result['details']['mentioned_prices'].append(f"RM {price}")
            logger.debug(f"Checking price: RM {price}")

            if price not in kb_prices:
                warning = f"⚠️ PRICE HALLUCINATION: RM {price} not found in knowledge base"
                logger.warning(warning)
                result['warnings'].append(warning)
                result['details']['suspicious_items'].append(f"Price: RM {price}")
                result['is_valid'] = False
                result['confidence'] -= 0.3

        # 2. Extract and validate product names
        logger.debug("Checking product names...")
        product_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*(?:\s+[Tt]-?shirt|[Dd]ress|[Jj]acket|[Pp]ants|[Ss]horts|[Ss]kirt|[Bb]louse|[Ss]weater|[Hh]oodie|[Cc]ardigan)?)'
        potential_products = re.findall(product_pattern, response_text)

        # Filter out common false positives
        exclude_words = {'Let', 'Thanks', 'Sure', 'Yes', 'No', 'Please', 'Hello',
                        'Hi', 'Great', 'Perfect', 'Would', 'Can', 'May', 'Should',
                        'Will', 'Cotton', 'Sizes', 'Colors', 'Price', 'Material'}

        for product in potential_products:
            if product.strip() and product not in exclude_words:
                result['details']['mentioned_products'].append(product)
                logger.debug(f"Checking product: {product}")

                product_lower = product.lower()
                if product_lower not in self.knowledge_base:
                    # Check for partial matches
                    words = product_lower.split()
                    if len(words) >= 2:  # Only flag multi-word product names
                        found = False
                        for word in words:
                            if len(word) > 3 and word in self.knowledge_base:
                                found = True
                                break

                        if not found:
                            warning = f"⚠️ PRODUCT HALLUCINATION: '{product}' not found in knowledge base"
                            logger.warning(warning)
                            result['warnings'].append(warning)
                            result['details']['suspicious_items'].append(f"Product: {product}")
                            result['is_valid'] = False
                            result['confidence'] -= 0.4

        # 3. Check for vague recommendations
        logger.debug("Checking for vague recommendations...")
        recommendation_phrases = [
            'we have', 'we\'ve got', 'available', 'in stock',
            'you can choose', 'you can get', 'check out', 'i recommend'
        ]

        has_recommendation = any(phrase in response_lower for phrase in recommendation_phrases)

        if has_recommendation and len(response_prices) == 0 and len(potential_products) > 0:
            warning = "⚠️ VAGUE RECOMMENDATION: Products mentioned without specific prices"
            logger.warning(warning)
            result['warnings'].append(warning)
            result['confidence'] -= 0.2

        # Ensure confidence doesn't go below 0
        result['confidence'] = max(0.0, result['confidence'])

        # Log final results
        logger.info("="*60)
        logger.info("VALIDATION RESULTS")
        logger.info("="*60)
        logger.info(f"Valid: {result['is_valid']}")
        logger.info(f"Confidence: {result['confidence']:.1%}")
        logger.info(f"Warnings: {len(result['warnings'])}")

        if result['warnings']:
            logger.warning("Warnings detected:")
            for warning in result['warnings']:
                logger.warning(f"  {warning}")

        logger.info(f"Mentioned prices: {result['details']['mentioned_prices']}")
        logger.info(f"Mentioned products: {len(result['details']['mentioned_products'])}")

        if result['details']['suspicious_items']:
            logger.warning(f"Suspicious items: {result['details']['suspicious_items']}")

        logger.info("="*60)

        return result

    def update_knowledge_base(self, new_knowledge_base: str) -> None:
        """
        Update the knowledge base

        Args:
            new_knowledge_base (str): New knowledge base content
        """
        logger.info("Updating knowledge base...")
        logger.debug(f"Previous KB size: {len(self.knowledge_base)} chars")
        logger.debug(f"New KB size: {len(new_knowledge_base)} chars")

        self.knowledge_base = new_knowledge_base.lower() if new_knowledge_base else ""
        self.has_kb = bool(new_knowledge_base)

        logger.info(f"✓ Knowledge base updated (has KB: {self.has_kb})")
