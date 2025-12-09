#!/usr/bin/env python3
"""
Script to add dynamic menu image sending via AI function calling

This will:
1. Add get_send_menu_image_function_definition() function
2. Add handle_send_menu_image_function_call() handler
3. Add the function to tools list
4. Add elif case in tool_calls processing
"""

# =============================================================================
# STEP 1: Function Definition (insert after line 745, before line 746)
# =============================================================================

FUNCTION_DEFINITION = '''

def get_send_menu_image_function_definition():
    """
    Define send_menu_image function for OpenAI function calling

    This tells OpenAI about the send_menu_image function and when/how to use it.
    Instead of static keyword matching, AI can intelligently detect when customer
    wants to see the menu/pricing and call this function dynamically.
    """
    return {
        "type": "function",
        "function": {
            "name": "send_menu_image",
            "description": "Send menu/price list image to customer when they ask about treatments, services, prices, packages, or want to see available options. Use this when customer asks questions like: 'What services do you offer?', 'Show me your prices', 'What treatments are available?', 'I want to see the menu', '有什么服务?', '价格多少?', etc. This function intelligently detects the customer's language preference and sends the appropriate menu (English or Chinese).",
            "parameters": {
                "type": "object",
                "properties": {
                    "language_preference": {
                        "type": "string",
                        "enum": ["english", "chinese", "auto"],
                        "description": "Preferred language for menu image. Use 'chinese' if customer message contains Chinese characters (汉字), 'english' for English text, or 'auto' to detect automatically based on message content."
                    },
                    "customer_question": {
                        "type": "string",
                        "description": "The customer's original question that triggered menu request (for logging and context)"
                    }
                },
                "required": ["language_preference", "customer_question"]
            }
        }
    }
'''

# =============================================================================
# STEP 2: Handler Function (insert after line 1148, before line 1149)
# =============================================================================

HANDLER_FUNCTION = '''

def handle_send_menu_image_function_call(
    function_args: dict,
    customer_phone: str,
    whatsapp_handler,
    config: dict
) -> dict:
    """
    Handle send_menu_image function call from AI

    This is called when AI decides customer wants to see the menu.
    It sends the appropriate menu image (English or Chinese) via WhatsApp.

    Args:
        function_args: Arguments from AI (language_preference, customer_question)
        customer_phone: Customer's WhatsApp phone number
        whatsapp_handler: WhatsApp handler instance for sending images
        config: Config dict containing menu_image URLs

    Returns:
        dict with success status and message for AI
    """
    logger.info("="*80)
    logger.info("🖼️  HANDLING SEND MENU IMAGE FUNCTION CALL")
    logger.info("="*80)

    # Extract function arguments provided by AI
    language_preference = function_args.get('language_preference', 'auto')
    customer_question = function_args.get('customer_question', '')

    logger.info(f"📋 Function Arguments from AI:")
    logger.info(f"   Language Preference: '{language_preference}'")
    logger.info(f"   Customer Question: '{customer_question[:100]}...'")
    logger.info(f"   Customer Phone: '{customer_phone}'")

    # Get menu configuration
    menu_config = config.get('menu_image', {})

    if not menu_config.get('enabled', False):
        logger.warning("⚠️ Menu image feature is disabled in config!")
        logger.info("="*80)
        return {
            "success": False,
            "message": "Menu image feature is currently disabled."
        }

    # Determine which menu URL to use
    if language_preference == 'chinese':
        menu_url = menu_config.get('chinese_url')
        lang_display = "Chinese"
    elif language_preference == 'english':
        menu_url = menu_config.get('english_url')
        lang_display = "English"
    else:  # auto-detect
        # Auto-detect based on customer question
        chinese_chars = sum(1 for char in customer_question if '\\u4e00' <= char <= '\\u9fff')
        total_chars = len([c for c in customer_question if c.strip()])

        if total_chars > 0 and (chinese_chars / total_chars) > 0.3:
            menu_url = menu_config.get('chinese_url')
            lang_display = "Chinese (auto-detected)"
        else:
            menu_url = menu_config.get('english_url')
            lang_display = "English (auto-detected)"

    if not menu_url:
        logger.error(f"❌ Menu URL not configured for language: {language_preference}")
        logger.error("="*80)
        return {
            "success": False,
            "message": f"Menu image URL not configured for {language_preference} language."
        }

    logger.info(f"📸 Sending {lang_display} menu image...")
    logger.info(f"   URL: {menu_url[:60]}...")

    # Send menu image via WhatsApp
    try:
        image_result = whatsapp_handler.send_image(
            to=customer_phone,
            image_url=menu_url
        )

        if image_result and image_result.get('sent'):
            logger.info(f"✅ MENU IMAGE SENT SUCCESSFULLY!")
            logger.info(f"   Language: {lang_display}")
            logger.info(f"   Recipient: {customer_phone}")
            logger.info("="*80)

            return {
                "success": True,
                "message": f"Menu image ({lang_display}) successfully sent to customer. You can now answer any specific questions they have about the treatments or prices shown in the menu."
            }
        else:
            logger.error(f"❌ FAILED TO SEND MENU IMAGE!")
            logger.error(f"   Result: {image_result}")
            logger.error("="*80)
            return {
                "success": False,
                "message": "Failed to send menu image. Please try describing the treatments verbally."
            }

    except Exception as e:
        logger.error(f"❌ EXCEPTION WHILE SENDING MENU IMAGE!")
        logger.error(f"   Error: {str(e)}")
        logger.error("="*80)
        return {
            "success": False,
            "message": f"Error sending menu image: {str(e)}"
        }
'''

# =============================================================================
# STEP 3: Add to tools list (modify line 1882-1887)
# =============================================================================

TOOLS_LIST_ADDITION = '''
        # Define available tools (escalation + member registration + booking + menu)
        tools = [
            get_escalation_function_definition(),
            get_register_member_function_definition(),
            get_record_booking_function_definition(),
            get_search_booking_function_definition(),
            get_send_menu_image_function_definition()  # NEW: Dynamic menu sending
        ]
'''

# =============================================================================
# STEP 4: Add handler case (insert after line 1967)
# =============================================================================

HANDLER_CASE = '''
                elif function_name == "send_menu_image":
                    menu_result = handle_send_menu_image_function_call(
                        function_args=function_args,
                        customer_phone=sender,
                        whatsapp_handler=whatsapp_handler,
                        config=config
                    )

                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(menu_result)
                    })
'''

# =============================================================================
# Print instructions
# =============================================================================

print("="*80)
print("DYNAMIC MENU IMAGE IMPLEMENTATION")
print("="*80)
print()
print("This script contains all code needed to add dynamic menu sending.")
print("Review the code sections below and apply them to your VPS:")
print()
print("STEP 1: Add function definition after line 745")
print("-" * 80)
print(FUNCTION_DEFINITION)
print()
print("STEP 2: Add handler function after line 1148")
print("-" * 80)
print(HANDLER_FUNCTION)
print()
print("STEP 3: Update tools list at line 1882-1887")
print("-" * 80)
print(TOOLS_LIST_ADDITION)
print()
print("STEP 4: Add handler case after line 1967")
print("-" * 80)
print(HANDLER_CASE)
print()
print("="*80)
print("BENEFITS OF DYNAMIC APPROACH:")
print("="*80)
print("✅ AI intelligently detects menu requests (not just keywords)")
print("✅ Works with natural language: 'What do you offer?', 'Show prices', etc.")
print("✅ Auto-detects language preference (English vs Chinese)")
print("✅ Better conversation flow - AI knows when menu was sent")
print("✅ Can handle variations: 'services', 'treatments', 'packages', etc.")
print()
print("TESTING:")
print("-" * 80)
print("Try these messages after implementation:")
print("  - 'What services do you have?' (should trigger menu)")
print("  - 'Show me your treatments' (should trigger menu)")
print("  - '有什么服务?' (should send Chinese menu)")
print("  - 'How much does foot reflexology cost?' (may or may not trigger)")
print()
print("="*80)
