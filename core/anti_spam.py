"""
Anti-Spam Protection System
Protects chat agent from spam, flooding, and abuse

Features:
- Rate limiting per user
- Flood detection
- Webhook signature verification
- User cooldown periods
- Automatic blocking and warnings
- IP-based throttling
"""

import time
import hmac
import hashlib
from typing import Dict, Optional, List, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, deque
from utils.logger import get_logger

logger = get_logger(__name__)


class AntiSpamManager:
    """
    Comprehensive anti-spam protection system

    Protections:
    1. Rate Limiting - Max messages per time window per user
    2. Flood Detection - Detects rapid repeated messages
    3. Cooldown Periods - Enforces delays between messages
    4. Automatic Blocking - Temporarily blocks abusive users
    5. Pattern Detection - Identifies spam patterns
    """

    def __init__(self, config: Dict = None):
        """
        Initialize Anti-Spam Manager

        Args:
            config: Configuration dict with spam protection settings
        """
        logger.info("="*80)
        logger.info("INITIALIZING ANTI-SPAM MANAGER")
        logger.info("="*80)

        # Default configuration
        default_config = {
            'rate_limit': {
                'enabled': True,
                'max_messages_per_minute': 10,
                'max_messages_per_hour': 100,
                'burst_window_seconds': 60,
                'burst_threshold': 5  # Max 5 messages in burst window
            },
            'flood_detection': {
                'enabled': True,
                'duplicate_threshold': 3,  # Same message X times = flood
                'duplicate_window_seconds': 60,
                'similarity_threshold': 0.8  # 80% similar = duplicate
            },
            'cooldown': {
                'enabled': True,
                'min_seconds_between_messages': 2,
                'escalate_cooldown_after_violations': True,
                'max_cooldown_seconds': 30
            },
            'blocking': {
                'enabled': True,
                'auto_block_after_violations': 5,
                'block_duration_minutes': 30,
                'warning_threshold': 3
            },
            'whitelist': [],  # Phone numbers to bypass all checks
            'blacklist': []   # Permanently blocked phone numbers
        }

        # Merge with provided config
        self.config = {**default_config, **(config or {})}

        # User tracking data structures
        self.user_messages: Dict[str, deque] = defaultdict(lambda: deque(maxlen=200))
        self.user_violations: Dict[str, int] = defaultdict(int)
        self.user_last_message: Dict[str, float] = {}
        self.user_cooldowns: Dict[str, float] = defaultdict(lambda: 2.0)  # Dynamic cooldowns
        self.blocked_users: Dict[str, float] = {}  # user_id -> unblock_time
        self.user_message_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=50))

        # IP tracking (for web chat)
        self.ip_requests: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.blocked_ips: Dict[str, float] = {}

        logger.info("Configuration loaded:")
        logger.info(f"  Rate Limiting: {self.config.get('rate_limit', {}).get('enabled', True)}")
        logger.info(f"    Max per minute: {self.config.get('rate_limit', {}).get('max_messages_per_minute', 10)}")
        logger.info(f"    Max per hour: {self.config.get('rate_limit', {}).get('max_messages_per_hour', 100)}")
        logger.info(f"  Flood Detection: {self.config.get('flood_detection', {}).get('enabled', True)}")
        logger.info(f"  Cooldown Periods: {self.config.get('cooldown', {}).get('enabled', True)}")
        logger.info(f"  Auto Blocking: {self.config.get('blocking', {}).get('enabled', True)}")
        logger.info(f"  Whitelisted Users: {len(self.config.get('whitelist', []))}")
        logger.info(f"  Blacklisted Users: {len(self.config.get('blacklist', []))}")
        logger.info("="*80)

    def check_message(self, user_id: str, message: str, ip_address: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Check if message should be allowed through spam filters

        Args:
            user_id: User identifier (phone number or session ID)
            message: Message content
            ip_address: Optional IP address (for web chat)

        Returns:
            Tuple of (allowed: bool, reason: Optional[str])
            - (True, None) if allowed
            - (False, "reason") if blocked
        """
        logger.debug("="*60)
        logger.debug(f"SPAM CHECK: {user_id[:20]}...")
        logger.debug("="*60)

        current_time = time.time()

        # 1. Check whitelist (bypass all checks)
        if user_id in self.config.get('whitelist', []):
            logger.debug("✅ User is whitelisted - bypassing all checks")
            return True, None

        # 2. Check blacklist (permanent block)
        if user_id in self.config.get('blacklist', []):
            logger.warning(f"🚫 User is blacklisted: {user_id}")
            return False, "You have been blocked from using this service. Please contact support."

        # 3. Check if user is temporarily blocked
        if user_id in self.blocked_users:
            unblock_time = self.blocked_users[user_id]
            if current_time < unblock_time:
                remaining = int(unblock_time - current_time)
                logger.warning(f"🚫 User is temporarily blocked: {user_id} ({remaining}s remaining)")
                return False, f"You have been temporarily blocked due to suspicious activity. Please try again in {remaining // 60} minutes."
            else:
                # Unblock user
                del self.blocked_users[user_id]
                logger.info(f"✅ User unblocked: {user_id}")

        # 4. Check IP blocking (web chat)
        if ip_address and ip_address in self.blocked_ips:
            unblock_time = self.blocked_ips[ip_address]
            if current_time < unblock_time:
                remaining = int(unblock_time - current_time)
                logger.warning(f"🚫 IP is blocked: {ip_address} ({remaining}s remaining)")
                return False, "Too many requests from your location. Please try again later."
            else:
                del self.blocked_ips[ip_address]

        # 5. Cooldown check
        if self.config.get('cooldown', {}).get('enabled', True):
            cooldown_result = self._check_cooldown(user_id, current_time)
            if not cooldown_result[0]:
                return cooldown_result

        # 6. Rate limiting check
        if self.config.get('rate_limit', {}).get('enabled', True):
            rate_limit_result = self._check_rate_limit(user_id, current_time)
            if not rate_limit_result[0]:
                self._record_violation(user_id, "rate_limit")
                return rate_limit_result

        # 7. Flood detection check
        if self.config.get('flood_detection', {}).get('enabled', True):
            flood_result = self._check_flood(user_id, message, current_time)
            if not flood_result[0]:
                self._record_violation(user_id, "flood")
                return flood_result

        # 8. IP rate limiting (web chat)
        if ip_address:
            ip_result = self._check_ip_rate_limit(ip_address, current_time)
            if not ip_result[0]:
                return ip_result

        # All checks passed - record message
        self.user_messages[user_id].append(current_time)
        self.user_last_message[user_id] = current_time
        self.user_message_history[user_id].append({
            'message': message[:100],  # Store first 100 chars
            'time': current_time
        })

        if ip_address:
            self.ip_requests[ip_address].append(current_time)

        logger.debug("✅ Message passed all spam checks")
        return True, None

    def _check_cooldown(self, user_id: str, current_time: float) -> Tuple[bool, Optional[str]]:
        """Check if user needs to wait before sending another message"""
        if user_id not in self.user_last_message:
            return True, None

        last_message_time = self.user_last_message[user_id]
        required_cooldown = self.user_cooldowns[user_id]
        time_since_last = current_time - last_message_time

        if time_since_last < required_cooldown:
            remaining = int(required_cooldown - time_since_last)
            logger.debug(f"⏳ Cooldown active: {remaining}s remaining")
            return False, f"Please wait {remaining} seconds before sending another message."

        return True, None

    def _check_rate_limit(self, user_id: str, current_time: float) -> Tuple[bool, Optional[str]]:
        """Check rate limits (per minute and per hour)"""
        messages = self.user_messages[user_id]

        # Count messages in last minute
        one_minute_ago = current_time - 60
        messages_last_minute = sum(1 for t in messages if t > one_minute_ago)

        max_per_minute = self.config.get('rate_limit', {}).get('max_messages_per_minute', 10)

        if messages_last_minute >= max_per_minute:
            logger.warning(f"⚠️ Rate limit exceeded: {messages_last_minute}/{max_per_minute} per minute")
            return False, f"You're sending messages too quickly. Maximum {max_per_minute} messages per minute."

        # Count messages in last hour
        one_hour_ago = current_time - 3600
        messages_last_hour = sum(1 for t in messages if t > one_hour_ago)

        max_per_hour = self.config.get('rate_limit', {}).get('max_messages_per_hour', 100)

        if messages_last_hour >= max_per_hour:
            logger.warning(f"⚠️ Hourly limit exceeded: {messages_last_hour}/{max_per_hour} per hour")
            return False, f"You've reached the maximum of {max_per_hour} messages per hour. Please try again later."

        # Burst detection (rapid fire)
        burst_window = self.config.get('rate_limit', {}).get('burst_window_seconds', 60)
        burst_threshold = self.config.get('rate_limit', {}).get('burst_threshold', 5)
        burst_cutoff = current_time - burst_window

        messages_in_burst = sum(1 for t in messages if t > burst_cutoff)

        if messages_in_burst >= burst_threshold:
            logger.warning(f"⚠️ Burst detected: {messages_in_burst} messages in {burst_window}s")
            return False, "Please slow down. You're sending messages too rapidly."

        return True, None

    def _check_flood(self, user_id: str, message: str, current_time: float) -> Tuple[bool, Optional[str]]:
        """Check for flood/spam patterns (repeated messages)"""
        history = self.user_message_history[user_id]

        if len(history) < 2:
            return True, None

        duplicate_window = self.config.get('flood_detection', {}).get('duplicate_window_seconds', 60)
        duplicate_threshold = self.config.get('flood_detection', {}).get('duplicate_threshold', 3)

        # Count similar messages in recent history
        recent_cutoff = current_time - duplicate_window
        recent_messages = [h['message'] for h in history if h['time'] > recent_cutoff]

        # Count exact duplicates
        duplicate_count = sum(1 for msg in recent_messages if msg.lower().strip() == message.lower().strip()[:100])

        if duplicate_count >= duplicate_threshold:
            logger.warning(f"🌊 Flood detected: {duplicate_count} duplicate messages")
            return False, "Please stop sending the same message repeatedly."

        # Check for very similar messages (spam variations)
        similarity_threshold = self.config.get('flood_detection', {}).get('similarity_threshold', 0.8)
        similar_count = 0

        for msg in recent_messages[-5:]:  # Check last 5 messages
            similarity = self._calculate_similarity(message[:100].lower(), msg.lower())
            if similarity >= similarity_threshold:
                similar_count += 1

        if similar_count >= duplicate_threshold:
            logger.warning(f"🌊 Spam pattern detected: {similar_count} similar messages")
            return False, "Please stop sending similar messages repeatedly."

        return True, None

    def _check_ip_rate_limit(self, ip_address: str, current_time: float) -> Tuple[bool, Optional[str]]:
        """Check IP-based rate limiting (web chat)"""
        requests = self.ip_requests[ip_address]

        # Max 30 requests per minute from same IP
        one_minute_ago = current_time - 60
        requests_last_minute = sum(1 for t in requests if t > one_minute_ago)

        if requests_last_minute >= 30:
            logger.warning(f"⚠️ IP rate limit: {ip_address} ({requests_last_minute} req/min)")

            # Block IP for 15 minutes
            self.blocked_ips[ip_address] = current_time + (15 * 60)

            return False, "Too many requests. Please try again in 15 minutes."

        return True, None

    def _record_violation(self, user_id: str, violation_type: str):
        """Record spam violation and auto-block if threshold reached"""
        self.user_violations[user_id] += 1
        violation_count = self.user_violations[user_id]

        logger.warning(f"⚠️ Violation recorded for {user_id}: {violation_type} (total: {violation_count})")

        # Escalate cooldown period
        if self.config.get('cooldown', {}).get('escalate_cooldown_after_violations', False):
            new_cooldown = min(
                self.user_cooldowns[user_id] * 1.5,
                self.config.get('cooldown', {}).get('max_cooldown_seconds', 30)
            )
            self.user_cooldowns[user_id] = new_cooldown
            logger.info(f"  Cooldown increased to {new_cooldown:.1f}s")

        # Issue warning
        warning_threshold = self.config.get('blocking', {}).get('warning_threshold', 3)
        if violation_count == warning_threshold:
            logger.warning(f"⚠️ WARNING THRESHOLD REACHED: {user_id}")

        # Auto-block if threshold reached
        if self.config.get('blocking', {}).get('enabled', False):
            block_threshold = self.config.get('blocking', {}).get('auto_block_after_violations', 5)

            if violation_count >= block_threshold:
                block_duration = self.config.get('blocking', {}).get('block_duration_minutes', 30) * 60
                self.blocked_users[user_id] = time.time() + block_duration

                logger.warning("="*80)
                logger.warning(f"🚫 AUTO-BLOCKED USER: {user_id}")
                logger.warning(f"   Violations: {violation_count}")
                logger.warning(f"   Duration: {self.config.get('blocking', {}).get('block_duration_minutes', 30)} minutes")
                logger.warning("="*80)

    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity between two strings (simple approach)"""
        if not text1 or not text2:
            return 0.0

        # Simple character-based similarity
        set1 = set(text1.split())
        set2 = set(text2.split())

        if not set1 or not set2:
            return 0.0

        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))

        return intersection / union if union > 0 else 0.0

    def whitelist_user(self, user_id: str):
        """Add user to whitelist (bypass all checks)"""
        if 'whitelist' not in self.config:
            self.config['whitelist'] = []
        if user_id not in self.config['whitelist']:
            self.config['whitelist'].append(user_id)
            logger.info(f"✅ User whitelisted: {user_id}")

    def blacklist_user(self, user_id: str):
        """Add user to blacklist (permanent block)"""
        if 'blacklist' not in self.config:
            self.config['blacklist'] = []
        if user_id not in self.config['blacklist']:
            self.config['blacklist'].append(user_id)
            logger.warning(f"🚫 User blacklisted: {user_id}")

    def unblock_user(self, user_id: str):
        """Manually unblock a user"""
        if user_id in self.blocked_users:
            del self.blocked_users[user_id]
            self.user_violations[user_id] = 0
            self.user_cooldowns[user_id] = 2.0
            logger.info(f"✅ User unblocked: {user_id}")
            return True
        return False

    def get_user_status(self, user_id: str) -> Dict:
        """Get spam protection status for a user"""
        current_time = time.time()
        messages = self.user_messages[user_id]

        # Count recent messages
        one_minute_ago = current_time - 60
        one_hour_ago = current_time - 3600

        return {
            'user_id': user_id,
            'whitelisted': user_id in self.config.get('whitelist', []),
            'blacklisted': user_id in self.config.get('blacklist', []),
            'blocked': user_id in self.blocked_users,
            'blocked_until': datetime.fromtimestamp(self.blocked_users[user_id]).isoformat() if user_id in self.blocked_users else None,
            'violations': self.user_violations[user_id],
            'current_cooldown': self.user_cooldowns[user_id],
            'messages_last_minute': sum(1 for t in messages if t > one_minute_ago),
            'messages_last_hour': sum(1 for t in messages if t > one_hour_ago),
            'total_messages': len(messages)
        }

    def cleanup_old_data(self):
        """Cleanup old tracking data (call periodically)"""
        current_time = time.time()
        cleanup_threshold = current_time - (24 * 3600)  # 24 hours

        # Cleanup old message tracking
        users_to_cleanup = []
        for user_id, messages in self.user_messages.items():
            if messages and messages[-1] < cleanup_threshold:
                users_to_cleanup.append(user_id)

        for user_id in users_to_cleanup:
            del self.user_messages[user_id]
            del self.user_message_history[user_id]
            if user_id in self.user_violations:
                del self.user_violations[user_id]
            if user_id in self.user_cooldowns:
                del self.user_cooldowns[user_id]
            if user_id in self.user_last_message:
                del self.user_last_message[user_id]

        # Cleanup expired blocks
        expired_blocks = [uid for uid, unblock_time in self.blocked_users.items() if current_time > unblock_time]
        for uid in expired_blocks:
            del self.blocked_users[uid]

        # Cleanup expired IP blocks
        expired_ips = [ip for ip, unblock_time in self.blocked_ips.items() if current_time > unblock_time]
        for ip in expired_ips:
            del self.blocked_ips[ip]

        if users_to_cleanup or expired_blocks or expired_ips:
            logger.info(f"🧹 Cleanup: {len(users_to_cleanup)} users, {len(expired_blocks)} blocks, {len(expired_ips)} IPs")


class WebhookValidator:
    """
    Webhook signature verification for Whapi
    Ensures webhooks are authentic and not forged
    """

    def __init__(self, webhook_secret: Optional[str] = None):
        """
        Initialize webhook validator

        Args:
            webhook_secret: Secret key for HMAC verification (from Whapi)
        """
        self.webhook_secret = webhook_secret
        self.enabled = bool(webhook_secret)

        if self.enabled:
            logger.info("✅ Webhook signature verification enabled")
        else:
            logger.warning("⚠️ Webhook signature verification disabled (no secret configured)")

    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify webhook signature using HMAC-SHA256

        Args:
            payload: Raw request body (bytes)
            signature: Signature from webhook header

        Returns:
            bool: True if signature is valid
        """
        if not self.enabled:
            logger.debug("Signature verification disabled - skipping")
            return True

        try:
            # Calculate expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()

            # Compare signatures (constant-time comparison)
            is_valid = hmac.compare_digest(signature, expected_signature)

            if is_valid:
                logger.debug("✅ Webhook signature valid")
            else:
                logger.warning("🚫 Webhook signature INVALID!")
                logger.warning(f"   Expected: {expected_signature[:20]}...")
                logger.warning(f"   Received: {signature[:20]}...")

            return is_valid

        except Exception as e:
            logger.error(f"❌ Error verifying webhook signature: {e}")
            return False
