# 🔧 Switching to OpenAI Function Calling for Escalation

## Overview

Changing from **Option 1 (Keyword Detection)** to **Option 2 (OpenAI Function Calling)** for more intelligent escalation.

---

## What Changes

### **Before (Keyword Detection):**
```python
# Check if AI response contains "I'll forward"
if "i'll forward" in assistant_message.lower():
    # Trigger escalation
    escalate_to_human(...)
```

### **After (Function Calling):**
```python
# AI engine analyzes and decides to call escalate_to_human function
ai_response = ai_engine.generate_response(messages, tools=[escalation_function_def])

# Check if AI wants to call function
if ai_response.get('tool_calls'):
    # Execute the function
    result = escalate_to_human(...)
    # Send result back to AI for final response
```

---

## Implementation Steps

### **Step 1: Define Escalation Function for OpenAI**

Create the function schema that tells OpenAI about the `escalate_to_human` function:

```python
# Add to web/app.py after init_app()
def get_escalation_function_definition():
    """
    Define escalation function for OpenAI function calling
    """
    return {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Escalate customer inquiry to human manager or staff member when unable to help. Use this when: customer needs special assistance, requests discount/group booking, has complaints, asks for manager, or inquiry requires human judgment.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_message": {
                        "type": "string",
                        "description": "The customer's original message or request"
                    },
                    "escalation_reason": {
                        "type": "string",
                        "description": "Brief reason why escalation is needed (e.g., 'special discount request', 'complaint about service', 'complex inquiry')"
                    },
                    "escalation_type": {
                        "type": "string",
                        "enum": ["special_request", "complaint", "membership", "system_issue", "general"],
                        "description": "Type of escalation: special_request (discounts/custom packages), complaint (service issues), membership (billing/points), system_issue (booking problems), general (other)"
                    }
                },
                "required": ["customer_message", "escalation_reason", "escalation_type"]
            }
        }
    }
```

### **Step 2: Update WhatsApp Webhook Handler**

Replace the keyword detection section with function calling:

```python
@app.route('/webhook/whapi', methods=['POST'])
def whapi_webhook():
    # ... (existing code for extracting message_data, sender, user_message) ...

    # Generate AI response WITH function calling enabled
    messages = conversation_manager.get_conversation_for_api(session_id)

    # Define available tools (escalation function)
    tools = [{
        "type": "function",
        "function": get_escalation_function_definition()['function']
    }]

    # Call AI with function calling enabled
    ai_response = ai_engine.generate_response(messages, tools=tools, tool_choice="auto")

    if not ai_response['success']:
        logger.error(f"AI response failed: {ai_response['error']}")
        return jsonify({'success': True}), 200

    # Check if AI wants to call escalation function
    tool_calls = ai_response.get('tool_calls')

    if tool_calls:
        logger.info("="*80)
        logger.info("🔧 AI IS CALLING FUNCTION")
        logger.info("="*80)

        # Process function calls
        function_results = []

        for tool_call in tool_calls:
            function_name = tool_call['function']['name']
            function_args = json.loads(tool_call['function']['arguments'])

            logger.info(f"Function: {function_name}")
            logger.debug(f"Arguments: {function_args}")

            if function_name == "escalate_to_human":
                # Execute escalation
                escalation_result = handle_escalation_function_call(
                    function_args=function_args,
                    customer_phone=sender,
                    customer_name=message_data.get('from_name', sender),
                    message_id=message_data.get('message_id', ''),
                    platform='whatsapp'
                )

                function_results.append({
                    "tool_call_id": tool_call['id'],
                    "role": "tool",
                    "name": function_name,
                    "content": json.dumps(escalation_result)
                })

        # Add function results to conversation
        messages.append({
            "role": "assistant",
            "tool_calls": tool_calls
        })
        messages.extend(function_results)

        # Get final response from AI after executing function
        final_response = ai_engine.generate_response(messages)
        assistant_message = final_response['content']

    else:
        # No function call, use AI's text response directly
        assistant_message = ai_response['content']

    # Add to conversation
    conversation_manager.add_message(session_id, 'assistant', assistant_message)

    # Send response via WhatsApp
    send_result = whatsapp_handler.send_message(sender, assistant_message)

    # ... (rest of the code)
```

### **Step 3: Create Function Call Handler**

Add new function to handle escalation function calls:

```python
def handle_escalation_function_call(
    function_args: Dict[str, Any],
    customer_phone: str,
    customer_name: str,
    message_id: str,
    platform: str
) -> Dict[str, Any]:
    """
    Handle escalation function call from AI

    Args:
        function_args: Arguments from AI (customer_message, escalation_reason, escalation_type)
        customer_phone: Customer's phone number
        customer_name: Customer's name
        message_id: Message ID for deduplication
        platform: 'whatsapp' or 'web'

    Returns:
        dict with success status and message for AI
    """
    logger.info("="*80)
    logger.info("🚨 HANDLING ESCALATION FUNCTION CALL")
    logger.info("="*80)

    # Extract function arguments
    customer_message = function_args.get('customer_message', '')
    escalation_reason = function_args.get('escalation_reason', '')
    escalation_type = function_args.get('escalation_type', 'general')

    logger.info(f"📋 Function Arguments:")
    logger.info(f"   Customer Message: '{customer_message[:100]}...'")
    logger.info(f"   Escalation Reason: '{escalation_reason}'")
    logger.info(f"   Escalation Type: '{escalation_type}'")

    # Create unique escalation ID to prevent duplicates
    escalation_id = f"{platform}_{customer_phone}_{message_id}"

    # Check if already escalated
    if escalation_id in escalated_messages:
        logger.info(f"⏭️ DUPLICATE ESCALATION DETECTED - SKIPPING")
        return {
            "success": False,
            "message": "This request has already been forwarded to the manager. They will contact you soon."
        }

    # Trigger escalation if tool is available
    if escalation_tool:
        logger.info(f"✓ Escalation tool available - executing...")

        escalation_result = escalation_tool.escalate_to_human(
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_message=customer_message,
            escalation_reason=escalation_reason,
            platform=platform,
            escalation_type=escalation_type
        )

        if escalation_result['success']:
            logger.info(f"✅ ESCALATION SUCCESSFUL!")
            logger.info(f"   Sent to: {escalation_result['manager']['name']}")

            # Mark as escalated to prevent duplicates
            escalated_messages.add(escalation_id)

            return {
                "success": True,
                "message": f"Request successfully forwarded to {escalation_result['manager']['name']} ({escalation_result['manager']['role']}). They will contact the customer at {customer_phone} shortly."
            }
        else:
            logger.error(f"❌ ESCALATION FAILED: {escalation_result.get('message')}")
            return {
                "success": False,
                "message": f"Unable to forward request: {escalation_result.get('message')}"
            }
    else:
        logger.warning("⚠️ Escalation tool not available!")
        return {
            "success": False,
            "message": "Escalation system is currently unavailable. Please contact us directly."
        }
```

### **Step 4: Remove Old Keyword Detection Code**

Delete the old escalation detection sections:

```python
# DELETE THIS ENTIRE SECTION (Lines ~600-700):
"""
# ===================================================================
# ESCALATION DETECTION - Auto-trigger if AI mentions forwarding
# ===================================================================
escalation_keywords = [
    'forward this to',
    ...
]

assistant_lower = assistant_message.lower()
if any(keyword in assistant_lower for keyword in escalation_keywords):
    # ... old keyword detection code ...
"""
```

---

## Key Benefits

1. **Intelligent Decision Making**
   - AI analyzes context, not just keywords
   - Can handle edge cases better

2. **Same Format & Spam Prevention**
   - Uses same `escalation_tool.escalate_to_human()` function
   - Same standardized message format
   - Same deduplication mechanism

3. **Better Accuracy**
   - AI decides WHEN to escalate
   - AI provides structured arguments
   - Less false positives

4. **Cleaner Code**
   - No keyword list to maintain
   - Function calling is built into OpenAI API
   - More maintainable

---

## Testing

After implementation, test:

1. **Basic escalation**: "Can I get discount for 20 people?"
2. **Complaint**: "The service was terrible"
3. **Complex inquiry**: "Do you have packages for pregnant women?"
4. **Normal inquiry**: "What is your price?" (should NOT escalate)
5. **Duplicate**: Send same escalation twice (should only send once)

---

##Files to Modify

1. **core/ai_engine.py** - ✅ DONE (added function calling support)
2. **web/app.py** - Need to implement:
   - Add `get_escalation_function_definition()`
   - Add `handle_escalation_function_call()`
   - Update WhatsApp webhook handler
   - Update web chat handler
   - Remove old keyword detection code

3. **config/prompts.yaml** - Update escalation instructions:
   ```yaml
   # Change from:
   "Tell customer you'll forward to manager"

   # To:
   "When you need to escalate, call the escalate_to_human function with appropriate parameters"
   ```

---

## Migration Plan

1. ✅ Update AI engine (DONE)
2. ⏳ Implement function calling in web/app.py
3. ⏳ Update prompts
4. ⏳ Test locally
5. ⏳ Deploy to VPS

**Status:** Ready to implement Step 2

