#!/usr/bin/env python3
"""
Implement Hybrid Menu Detection System
- Static keyword check (fast)
- AI intent detection (smart)
- Duplicate prevention
"""

import sys
import re

file_path = "/root/reflexology-agent(token-optimized)/web/app.py"

print("="*80)
print("IMPLEMENTING HYBRID MENU DETECTION SYSTEM")
print("="*80)

# Read the file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup
with open(file_path + '.backup_hybrid', 'w', encoding='utf-8') as f:
    f.write(content)
print("✅ Backup created: app.py.backup_hybrid")

# ============================================================================
# STEP 1: Add function definition
# ============================================================================
print("\n📝 STEP 1: Adding send_menu_image function definition...")

step1_code = '''

def get_send_menu_image_function_definition():
    """
    Define send_menu_image function for OpenAI function calling

    AI can intelligently detect when customer wants to see menu/prices
    and call this function instead of relying only on static keywords.
    """
    return {
        "type": "function",
        "function": {
            "name": "send_menu_image",
            "description": "Send menu/price list image when customer asks about services, treatments, prices, or packages. Use when customer says things like: 'what services do you have?', 'show me treatments', 'how much does it cost?', '有什么服务?', 'what do you offer?', 'I want to see your menu', etc. This intelligently detects language and sends appropriate menu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "language_preference": {
                        "type": "string",
                        "enum": ["english", "chinese", "auto"],
                        "description": "Preferred language for menu. Use 'chinese' if customer message contains Chinese characters, 'english' for English text, or 'auto' to auto-detect based on message content."
                    }
                },
                "required": ["language_preference"]
            }
        }
    }
'''

# Find insertion point after get_search_booking_function_definition
pattern1 = r'(def get_search_booking_function_definition\(\):.*?return \{[^}]+\}[^}]+\}[^}]+\}\n)'
match1 = re.search(pattern1, content, re.DOTALL)

if match1:
    insert_pos = match1.end()
    content = content[:insert_pos] + step1_code + content[insert_pos:]
    print("✅ Step 1: Function definition added")
else:
    print("⚠️  Trying alternative insertion point...")
    pattern1_alt = r'(def get_register_member_function_definition\(\):.*?return \{[^}]+\}[^}]+\}[^}]+\}\n)'
    match1_alt = re.search(pattern1_alt, content, re.DOTALL)
    if match1_alt:
        insert_pos = match1_alt.end()
        content = content[:insert_pos] + step1_code + content[insert_pos:]
        print("✅ Step 1: Function definition added (alt)")
    else:
        print("❌ Step 1 FAILED")
        sys.exit(1)

# ============================================================================
# STEP 2: Add handler function
# ============================================================================
print("\n📝 STEP 2: Adding handler function...")

step2_code = '''

def handle_send_menu_image_function_call(function_args, customer_phone, whatsapp_handler, config, user_message):
    """Handle send_menu_image function call from AI"""
    logger.info("="*80)
    logger.info("🖼️  AI CALLED send_menu_image FUNCTION")
    logger.info("="*80)

    language_pref = function_args.get('language_preference', 'auto')
    menu_config = config.get('menu_image', {})

    if not menu_config.get('enabled', False):
        return {"success": False, "message": "Menu feature disabled"}

    # Auto-detect language
    if language_pref == 'auto':
        chinese_chars = sum(1 for c in user_message if u'\\u4e00' <= c <= u'\\u9fff')
        total_chars = len([c for c in user_message if c.strip()])
        language_pref = 'chinese' if (total_chars > 0 and chinese_chars/total_chars > 0.3) else 'english'

    # Get menu URL
    menu_url = menu_config.get('chinese_url' if language_pref == 'chinese' else 'english_url')
    caption = menu_config.get('caption_chinese' if language_pref == 'chinese' else 'caption_english', '')

    if not menu_url:
        logger.error(f"❌ Menu URL not configured for {language_pref}")
        return {"success": False, "message": f"Menu URL not configured"}

    logger.info(f"📸 Sending {language_pref} menu to {customer_phone}")

    try:
        result = whatsapp_handler.send_image(to=customer_phone, image_url=menu_url, caption=caption)
        if result and result.get('sent'):
            logger.info("✅ Menu sent via AI function!")
            logger.info("="*80)
            return {"success": True, "message": f"Menu ({language_pref}) sent. Answer their questions about it."}
        else:
            logger.error(f"❌ Failed: {result}")
            logger.error("="*80)
            return {"success": False, "message": "Failed to send menu"}
    except Exception as e:
        logger.error(f"❌ Exception: {e}")
        logger.error("="*80)
        return {"success": False, "message": str(e)}
'''

# Find insertion after handle_search_booking_function_call
pattern2 = r'(def handle_search_booking_function_call\([^)]+\)[^:]+:.*?(?=\n\ndef|\nclass|\n# =|\Z))'
match2 = re.search(pattern2, content, re.DOTALL)

if match2:
    insert_pos = match2.end()
    content = content[:insert_pos] + step2_code + content[insert_pos:]
    print("✅ Step 2: Handler function added")
else:
    print("❌ Step 2 FAILED")
    sys.exit(1)

# ============================================================================
# STEP 3: Add tracking variable
# ============================================================================
print("\n📝 STEP 3: Adding tracking variable...")

step3_old = """        menu_config = config.get('menu_image', {})
        # Allow menu detection for both text and voice messages (voice gets transcribed to user_message)
        if menu_config.get('enabled', False) and user_message:"""

step3_new = """        # Track if menu sent via static keywords (prevent AI duplicate)
        menu_sent_via_static = False

        menu_config = config.get('menu_image', {})
        # Allow menu detection for both text and voice messages (voice gets transcribed to user_message)
        if menu_config.get('enabled', False) and user_message:"""

if step3_old in content:
    content = content.replace(step3_old, step3_new)
    print("✅ Step 3: Tracking variable added")

    # Also mark when static menu sent
    step3b_old = """            if detect_menu_request(user_message, keywords):
                logger.info("=" * 80)
                logger.info("🖼️  MENU REQUEST DETECTED - SENDING MENU IMAGE")"""

    step3b_new = """            if detect_menu_request(user_message, keywords):
                menu_sent_via_static = True
                logger.info("=" * 80)
                logger.info("🖼️  STATIC KEYWORD DETECTED - SENDING MENU IMAGE")"""

    content = content.replace(step3b_old, step3b_new)
    print("✅ Step 3b: Flag setting added")
else:
    print("❌ Step 3 FAILED")
    sys.exit(1)

# ============================================================================
# STEP 4: Add to tools list
# ============================================================================
print("\n📝 STEP 4: Adding to tools list...")

step4_old = """        tools = [
            get_escalation_function_definition(),
            get_register_member_function_definition(),
            get_record_booking_function_definition(),
            get_search_booking_function_definition()
        ]"""

step4_new = """        tools = [
            get_escalation_function_definition(),
            get_register_member_function_definition(),
            get_record_booking_function_definition(),
            get_search_booking_function_definition(),
            get_send_menu_image_function_definition()
        ]"""

if step4_old in content:
    content = content.replace(step4_old, step4_new)
    print("✅ Step 4: Added to tools list")
else:
    print("❌ Step 4 FAILED")
    sys.exit(1)

# ============================================================================
# STEP 5: Add handler case
# ============================================================================
print("\n📝 STEP 5: Adding handler case...")

step5_code = '''

                elif function_name == "send_menu_image":
                    # Check if menu already sent via static keywords
                    if menu_sent_via_static:
                        logger.info("⏭️  Menu already sent via static - skipping AI send")
                        menu_result = {"success": True, "message": "Menu already sent. Answer their questions."}
                    else:
                        menu_result = handle_send_menu_image_function_call(
                            function_args=function_args,
                            customer_phone=sender,
                            whatsapp_handler=whatsapp_handler,
                            config=config,
                            user_message=user_message
                        )

                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(menu_result)
                    })'''

# Find search_booking elif block
pattern5 = r'(elif function_name == "search_booking":.*?function_results\.append\(\{[^}]+\}\))'
match5 = re.search(pattern5, content, re.DOTALL)

if match5:
    insert_pos = match5.end()
    content = content[:insert_pos] + step5_code + content[insert_pos:]
    print("✅ Step 5: Handler case added")
else:
    print("❌ Step 5 FAILED")
    sys.exit(1)

# Write back
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*80)
print("✅ ALL STEPS COMPLETED!")
print("="*80)
print("Changes:")
print("  ✅ Function definition")
print("  ✅ Handler function")
print("  ✅ Tracking variable")
print("  ✅ Tools list updated")
print("  ✅ Handler case with duplicate check")
print("\nHybrid menu system ready!")
print("="*80)
