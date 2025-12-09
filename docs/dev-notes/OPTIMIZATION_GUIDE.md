# Serenity Reflexology Agent - Token Optimization Guide

## Summary of Changes

This document describes the optimizations made to reduce token consumption by ~75%.

### Token Savings Breakdown

| Component | Before | After | Savings |
|-----------|--------|-------|---------|
| System Prompt | ~6,000 tokens | ~1,600 tokens | 73% |
| Knowledge Base | ~8,000 tokens | ~2,800 tokens | 65% |
| Conversation History | ~5,000 tokens (50 msgs) | ~2,000 tokens (20 msgs) | 60% |
| Memory Context | ~1,000 tokens | ~200 tokens | 80% |
| AI Calls per Message | 4 calls | 1.5 avg | 62% |
| **TOTAL per Message** | **~21,000 tokens** | **~6,000 tokens** | **71%** |

---

## Files Changed/Added

### Modified Files:

1. **`core/conversation_manager.py`**
   - Reduced `max_history_length` from 50 to 20
   - Added `summarize_if_needed()` method for automatic conversation summarization
   - Added token estimation utilities

2. **`core/ai_engine.py`**
   - Added `model` parameter to `generate_response()` for using gpt-4o-mini

### New Files:

3. **`config/prompts/whatsapp_with_knowledge_optimized.txt`**
   - Cleaned system prompt (~75% smaller)
   - Removed duplicated content (cupping/gua sha templates, menu)
   - Condensed examples and instructions

4. **`data/knowledge_base/catalog_optimized.txt`**
   - Single-language content (AI translates)
   - Removed duplicate Chinese/English sections
   - Streamlined structure

5. **`utils/extraction_optimizer.py`**
   - Combined extraction (interest + preferences + summary in ONE call)
   - Milestone-based extraction (not every message)
   - Uses gpt-4o-mini for cost efficiency

6. **`utils/token_optimizer.py`**
   - Message restructuring for OpenAI prompt caching
   - Selective KB section retrieval
   - Memory context compression

---

## How to Integrate

### Step 1: Update Configuration

In your `config/config.json`, update the prompt file path:

```json
{
  "prompts": {
    "whatsapp": "config/prompts/whatsapp_with_knowledge_optimized.txt"
  },
  "knowledge_base": {
    "path": "data/knowledge_base/catalog_optimized.txt"
  }
}
```

### Step 2: Update app.py Imports

Add these imports at the top of `web/app.py`:

```python
from utils.extraction_optimizer import extraction_optimizer
from utils.token_optimizer import token_optimizer, log_token_usage
```

### Step 3: Update Message Construction

Replace the current message construction (around line 1817) with:

```python
# BEFORE (current code):
# memory_context = { ... }
# messages_with_memory = [messages[0], memory_context] + messages[1:]

# AFTER (optimized):
# Get conversation without system message
conversation_only = conversation_manager.get_conversation_for_api(session_id)[1:]

# Compress memory context
compressed_memory = ""
if customer_memory:
    compressed_memory = token_optimizer.compress_memory_context(customer_memory)

# Get relevant KB sections only (optional - for further savings)
# relevant_kb = token_optimizer.get_relevant_kb_sections(knowledge_base, user_message)

# Structure for caching
messages = token_optimizer.structure_messages_for_caching(
    system_prompt=system_prompt,
    knowledge_base=knowledge_base,  # or relevant_kb for more savings
    memory_context=compressed_memory,
    conversation=conversation_only
)

# Log token usage (for debugging)
log_token_usage(system_prompt, knowledge_base, compressed_memory, conversation_only)
```

### Step 4: Update Extraction Logic

Replace the extraction section (around lines 2011-2119) with:

```python
# BEFORE (current code - 3-4 separate AI calls):
# lead_info = lead_manager.extract_lead_info_from_conversation(...)
# summary_response = ai_engine.generate_response(...)
# preferences = lead_manager.extract_preferences(...)

# AFTER (optimized - 1 combined call, only at milestones):
if lead_manager and config.get('lead_tracking.enabled', False):
    messages = conversation_manager.get_conversation_for_api(session_id)

    # Check if extraction should run (milestones + triggers)
    should_extract = extraction_optimizer.should_extract(
        session_id=session_id,
        message_count=len(messages),
        last_user_message=user_message
    )

    if should_extract:
        # Combined extraction - ONE API call using gpt-4o-mini
        extraction_result = extraction_optimizer.extract_all(
            messages=messages,
            customer_phone=customer_phone,
            ai_engine=ai_engine,
            session_id=session_id
        )

        if extraction_result['success']:
            # Use results
            current_interest = extraction_result.get('interest', 'Initial contact')
            preferences = extraction_result.get('preferences', '')
            summary = extraction_result.get('summary', '')

            # Record to Google Sheets
            lead_manager.record_lead(
                customer_phone=customer_phone,
                customer_name=customer_name,
                current_interest=current_interest
            )

            # Save summary to history
            if summary:
                lead_manager.add_conversation_to_history(
                    phone=customer_phone,
                    conversation_summary=summary,
                    category=current_interest
                )

            # Update preferences
            if preferences:
                # Update in sheet...
                pass
    else:
        logger.debug("Extraction skipped - not at milestone")
```

### Step 5: Add Conversation Summarization

After processing each message, add summarization check:

```python
# After adding AI response to conversation history
conversation_manager.add_message(session_id, "assistant", ai_response)

# Check if conversation needs summarization (reduces tokens for long conversations)
conversation_manager.summarize_if_needed(session_id, ai_engine)
```

### Step 6: Use gpt-4o-mini for Auxiliary Tasks

For any auxiliary AI calls (not the main response), use the cheaper model:

```python
# For summarization, extraction, analysis - use gpt-4o-mini
response = ai_engine.generate_response(
    messages=[{"role": "user", "content": prompt}],
    model="gpt-4o-mini",  # 50% cheaper
    temperature=0.3,
    max_tokens=150
)

# For main customer response - keep using gpt-4o
main_response = ai_engine.generate_response(
    messages=messages,
    tools=tools,
    # model not specified = uses default gpt-4o
)
```

---

## Configuration Options

### Extraction Optimizer Settings

In `utils/extraction_optimizer.py`, you can adjust:

```python
# When to run extraction
EXTRACTION_MILESTONES = [5, 10, 15, 20]  # Message counts

# Trigger words for immediate extraction
EXTRACTION_TRIGGERS = ['done', 'confirmed', 'booked', ...]

# Minimum time between extractions
min_extraction_interval = 120  # seconds
```

### Conversation Manager Settings

```python
# Maximum messages to keep
max_history_length = 20  # Down from 50

# Token threshold for summarization
summarization_threshold = 3000  # Trigger summarization when exceeded
```

---

## Expected Results

### Before Optimization:
- 2,000,000 tokens for 50-60 conversations
- ~33,000-40,000 tokens per conversation
- 4 AI calls per message

### After Optimization:
- ~500,000-600,000 tokens for same volume
- ~8,000-10,000 tokens per conversation
- 1.5 AI calls per message average

### Cost Reduction:
- **~70-75% reduction in API costs**
- Additional 50% savings from OpenAI prompt caching on static content

---

## Testing

1. **Verify prompt loading:**
   ```python
   # Check token count of new prompt
   with open('config/prompts/whatsapp_with_knowledge_optimized.txt') as f:
       content = f.read()
       print(f"Prompt tokens: ~{len(content)//4}")
   ```

2. **Monitor extraction frequency:**
   - Check logs for "COMBINED EXTRACTION" entries
   - Should appear only at milestones, not every message

3. **Verify summarization:**
   - Long conversations should show "SUMMARIZING CONVERSATION" in logs
   - Message count should stay around 10-12 after summarization

4. **Check token usage:**
   - Enable `log_token_usage()` calls
   - Total should be ~6,000-8,000 per message (down from ~21,000)

---

## Rollback

If issues occur, revert to original files:

1. Use `whatsapp_with_knowledge.txt` instead of optimized version
2. Use `catalog.txt` instead of optimized version
3. Set `max_history_length = 50` in conversation_manager.py
4. Remove extraction_optimizer imports and use original extraction logic
