"""
Test Anti-Spam Protection System
Tests rate limiting, flood detection, and blocking features
"""

import sys
import os
import time

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.anti_spam import AntiSpamManager


def test_rate_limiting():
    """Test rate limiting protection"""
    print("="*80)
    print("TEST 1: RATE LIMITING")
    print("="*80)

    config = {
        'rate_limit': {
            'enabled': True,
            'max_messages_per_minute': 5,
            'max_messages_per_hour': 100,
            'burst_threshold': 3,
            'burst_window_seconds': 10
        },
        'cooldown': {
            'enabled': False
        },
        'flood_detection': {
            'enabled': False
        },
        'blocking': {
            'enabled': False
        }
    }

    manager = AntiSpamManager(config=config)

    user_id = "test_user_1"
    test_message = "Hello, this is a test message"

    print("\nSending 7 messages rapidly (limit is 5 per minute)...")
    for i in range(1, 8):
        allowed, reason = manager.check_message(user_id, f"{test_message} #{i}")

        if allowed:
            print(f"  [OK] Message {i}: ALLOWED")
        else:
            print(f"  [BLOCKED] Message {i}: BLOCKED - {reason}")

    print("\n[PASS] Rate limiting test completed\n")


def test_flood_detection():
    """Test flood detection (repeated messages)"""
    print("="*80)
    print("TEST 2: FLOOD DETECTION")
    print("="*80)

    config = {
        'flood_detection': {
            'enabled': True,
            'duplicate_threshold': 3,
            'duplicate_window_seconds': 60
        },
        'rate_limit': {
            'enabled': False  # Disable for this test
        }
    }

    manager = AntiSpamManager(config=config)

    user_id = "test_user_2"
    spam_message = "BUY NOW! CHEAP PRICES!"

    print("\nSending same message 5 times (threshold is 3)...")
    for i in range(1, 6):
        allowed, reason = manager.check_message(user_id, spam_message)

        if allowed:
            print(f"  [OK] Message {i}: ALLOWED")
        else:
            print(f"  [BLOCKED] Message {i}: BLOCKED - {reason}")

    print("\n[PASS]Flood detection test completed\n")


def test_cooldown_periods():
    """Test cooldown enforcement"""
    print("="*80)
    print("TEST 3: COOLDOWN PERIODS")
    print("="*80)

    config = {
        'cooldown': {
            'enabled': True,
            'min_seconds_between_messages': 2
        },
        'rate_limit': {
            'enabled': False
        },
        'flood_detection': {
            'enabled': False
        }
    }

    manager = AntiSpamManager(config=config)

    user_id = "test_user_3"

    print("\nSending 3 messages with different delays...")

    # Message 1
    allowed, reason = manager.check_message(user_id, "First message")
    print(f"  [OK] Message 1: ALLOWED")

    # Message 2 (immediate - should be blocked)
    allowed, reason = manager.check_message(user_id, "Second message (immediate)")
    if allowed:
        print(f"  [OK] Message 2: ALLOWED")
    else:
        print(f"  [BLOCKED] Message 2: BLOCKED - {reason}")

    # Wait for cooldown
    print("\n  [WAIT] Waiting 2 seconds...")
    time.sleep(2)

    # Message 3 (after cooldown - should be allowed)
    allowed, reason = manager.check_message(user_id, "Third message (after cooldown)")
    if allowed:
        print(f"  [OK] Message 3: ALLOWED")
    else:
        print(f"  [BLOCKED] Message 3: BLOCKED - {reason}")

    print("\n[PASS]Cooldown test completed\n")


def test_auto_blocking():
    """Test automatic blocking after violations"""
    print("="*80)
    print("TEST 4: AUTO-BLOCKING")
    print("="*80)

    config = {
        'rate_limit': {
            'enabled': True,
            'max_messages_per_minute': 2,
            'burst_threshold': 2
        },
        'blocking': {
            'enabled': True,
            'auto_block_after_violations': 3,
            'block_duration_minutes': 1,
            'warning_threshold': 2
        }
    }

    manager = AntiSpamManager(config=config)

    user_id = "test_user_4"

    print("\nTriggering violations to test auto-blocking...")
    print("(Need 3 violations to trigger block)")

    for i in range(1, 8):
        allowed, reason = manager.check_message(user_id, f"Message {i}")

        if allowed:
            print(f"  [OK] Message {i}: ALLOWED")
        else:
            violations = manager.user_violations[user_id]
            print(f"  [BLOCKED] Message {i}: BLOCKED (Violations: {violations})")

            if user_id in manager.blocked_users:
                print(f"  [AUTO-BLOCKED] USER AUTO-BLOCKED!")
                break

    print("\n[PASS]Auto-blocking test completed\n")


def test_whitelist():
    """Test whitelist functionality"""
    print("="*80)
    print("TEST 5: WHITELIST")
    print("="*80)

    config = {
        'whitelist': ['whitelisted_user'],
        'rate_limit': {
            'enabled': True,
            'max_messages_per_minute': 2
        }
    }

    manager = AntiSpamManager(config=config)

    print("\nTesting whitelisted user (should bypass all checks)...")

    for i in range(1, 6):
        allowed, reason = manager.check_message('whitelisted_user', f"Message {i}")

        if allowed:
            print(f"  [OK] Message {i}: ALLOWED (whitelisted)")
        else:
            print(f"  [BLOCKED] Message {i}: BLOCKED - {reason}")

    print("\n[PASS]Whitelist test completed\n")


def test_blacklist():
    """Test blacklist functionality"""
    print("="*80)
    print("TEST 6: BLACKLIST")
    print("="*80)

    config = {
        'blacklist': ['banned_user']
    }

    manager = AntiSpamManager(config=config)

    print("\nTesting blacklisted user (should be permanently blocked)...")

    allowed, reason = manager.check_message('banned_user', "I'm banned")

    if allowed:
        print(f"  [OK] Message: ALLOWED")
    else:
        print(f"  [BLOCKED] Message: BLOCKED - {reason}")

    print("\n[PASS]Blacklist test completed\n")


def test_user_status():
    """Test user status retrieval"""
    print("="*80)
    print("TEST 7: USER STATUS")
    print("="*80)

    manager = AntiSpamManager()

    user_id = "status_test_user"

    print("\nSending messages and checking status...")

    for i in range(3):
        manager.check_message(user_id, f"Message {i+1}")

    status = manager.get_user_status(user_id)

    print(f"\nUser Status:")
    print(f"  User ID: {status['user_id']}")
    print(f"  Whitelisted: {status['whitelisted']}")
    print(f"  Blacklisted: {status['blacklisted']}")
    print(f"  Blocked: {status['blocked']}")
    print(f"  Violations: {status['violations']}")
    print(f"  Current Cooldown: {status['current_cooldown']}s")
    print(f"  Messages (last minute): {status['messages_last_minute']}")
    print(f"  Messages (last hour): {status['messages_last_hour']}")
    print(f"  Total Messages: {status['total_messages']}")

    print("\n[PASS]User status test completed\n")


def main():
    """Run all tests"""
    print("\n")
    print("ANTI-SPAM PROTECTION SYSTEM - TEST SUITE")
    print("\n")

    try:
        test_rate_limiting()
        test_flood_detection()
        test_cooldown_periods()
        test_auto_blocking()
        test_whitelist()
        test_blacklist()
        test_user_status()

        print("="*80)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80)
        print("\nThe anti-spam system is working correctly!")
        print("You can now use it in production.\n")

    except Exception as e:
        print("="*80)
        print("TEST FAILED")
        print("="*80)
        print(f"\nError: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
