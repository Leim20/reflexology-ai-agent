# Error Documentation & Lessons Learned

**Project:** Reflexology Agent
**Date:** December 2024
**Purpose:** Document errors made during development to understand root causes and prevent recurrence.

---

## Error 0: Individual Cell Reads (1 Cell = 1 API Request)

*Previous fix from late November 2024*

### What Happened
Google Sheets API quota (60 requests/minute) was being exceeded during normal operation, even with only a few customer messages.

### Root Cause
The code used an inefficient pattern for looking up customer data:

**Bad Pattern (N+1 Query Problem):**
```
findall("phone_number")     → 1 API request
row_values(cell.row)        → 1 API request per match
row_values(cell.row)        → 1 API request per match
...
Total: 1 + N requests (where N = number of matches)
```

For example, looking up one customer could trigger 5+ API requests if the phone number appeared in multiple rows or cells.

**Additional Bad Pattern (Individual Cell Updates):**
```
update_cell(row, 1, name)      → 1 API request
update_cell(row, 2, phone)     → 1 API request
update_cell(row, 3, interest)  → 1 API request
...
Total: 8 requests to update 8 fields
```

### Why I Made This Mistake
- Used the "obvious" gspread API methods without understanding their quota cost
- Didn't realize each cell operation = 1 API request
- Assumed the library would batch operations automatically
- Didn't read Google Sheets API documentation about quota costs

### Lesson Learned
> **Each Google Sheets API call costs quota, regardless of data size.** Reading 1 cell costs the same as reading 1000 cells in a single `get_all_values()` call. Always prefer bulk operations over individual cell operations.

### Solution Implemented

**Problem:** Each `findall()` and `row_values()` call = 1 API request. Looking up 1 customer could trigger 5+ requests.

**Solution:**
1. **Bulk Read:** Instead of searching cell-by-cell, load the entire sheet once with `get_all_values()`, then filter in Python code. This costs 1 API request regardless of how many customers you search for.

2. **Bulk Write:** Instead of updating cells one-by-one, collect all changes and send them in a single `update_cells()` batch request.

3. **Caching:** Store frequently-accessed data (like customer records, members list) in memory with a TTL (time-to-live). Subsequent reads hit the cache (0 API calls) until cache expires.

**Result:** Reduced from 5+ API calls per lookup to 1 API call, plus caching reduces repeated lookups to 0.

### Prevention
- Use `get_all_values()` instead of `findall()` + `row_values()`
- Use `update_cells(batch)` instead of multiple `update_cell()` calls
- Add caching layer to avoid repeated reads of the same data
- Monitor API quota usage in logs

### Related Documentation
- `API_QUOTA_ANALYSIS.md` - Full quota breakdown
- `SHEET_READ_BREAKDOWN.md` - Which sheets consume most quota

---

## Error 1: Google Sheets API Burst Limit

### What Happened
Service failed to start properly. Google Sheets API returned 429 (Quota Exceeded) errors during initialization. Follow-up and Broadcast managers failed to initialize.

### Root Cause
Three managers (LeadManager, FollowUpManager, BroadcastManager) initialized simultaneously at startup, each making 5-9 API calls. With 2 Gunicorn workers, this resulted in ~42 API calls within 2 seconds.

Google Sheets API has two types of limits:
- **Per-minute limit:** 60 requests (we were within this)
- **Per-second burst limit:** ~10-20 requests (we exceeded this)

### Why I Made This Mistake
- Focused only on per-minute quota, unaware of per-second burst limits
- Didn't consider that service restart triggers all initialization at once
- Cache implementation only protects normal operation, not cold starts

### Lesson Learned
> **API rate limits have multiple dimensions.** Always consider both sustained limits (per minute/hour) AND burst limits (per second). Cold starts and restarts are vulnerable moments when caching cannot help.

### Solution Implemented

**Problem:** 3 managers start simultaneously, each making 5-9 API calls = 42 calls in 2 seconds.

**Solution:**
1. **Add Delays:** Insert `time.sleep(2)` between each manager initialization. This spreads 42 API calls over ~15 seconds instead of 2 seconds, staying under the per-second burst limit.

2. **Gunicorn Preload:** Add `--preload` flag to Gunicorn so the application initializes once in the master process, then forks to workers. This prevents 2 workers from each triggering 42 API calls separately.

**Result:** Service starts in ~15 seconds with no 429 errors. Managers initialize sequentially, respecting burst limits.

### Prevention
- Add delays between sequential API-heavy operations during initialization
- Use `--preload` in Gunicorn to initialize once instead of per-worker
- Test service restarts, not just normal operation

---

## Error 2: Token Waste in Extraction Functions

### What Happened
OpenAI API costs were unexpectedly high. 5 test conversations cost $0.25 instead of expected ~$0.05.

### Root Cause
The `analyze_interest` and `extract_preferences` functions were building conversation text from ALL messages, including system messages. The system message contained a 42KB knowledge base (~22,000 tokens).

These functions only needed to read what the customer and agent said, but were sending the entire knowledge base with every extraction call - which happened 2-3 times per customer message.

### Why I Made This Mistake
- Copy-pasted message iteration logic without considering what data each function actually needed
- Didn't think about what "messages" contained - assumed it was just conversation
- Didn't monitor token usage per API call type

### Lesson Learned
> **Understand what data each function actually needs.** Don't blindly pass everything available. System prompts and knowledge bases should only go where they're needed for response generation, not for simple text extraction tasks.

### Solution Implemented

**Problem:** Extraction functions iterated through ALL messages including system messages (which contain the 42KB knowledge base).

**Solution:**
When building conversation text for extraction, add a filter to skip system messages:
- Check the message role
- If role is "system", skip it and continue to next message
- Only include "user" and "assistant" messages in the extraction

**Result:** Extraction calls reduced from ~22,000 tokens to ~500 tokens (95% reduction). These functions only see the actual conversation, not the knowledge base they don't need.

### Prevention
- Before passing data to AI, ask: "Does this function need ALL this information?"
- Log token usage per function type to identify waste
- Review functions that iterate over messages - filter appropriately

---

## Error 3: Incomplete Function Implementation

### What Happened
Customer bookings were not being recorded to Google Sheets despite successful conversations.

### Root Cause
The `handle_record_booking_function_call` function was incomplete. It:
1. Extracted all booking details from parameters ✓
2. Validated that all required fields existed ✓
3. **Never called `lead_manager.record_booking()` to actually save** ✗

The code to save the booking existed but was orphaned outside the function (unreachable dead code).

### Why I Made This Mistake
- Likely interrupted during development and forgot to complete the function
- No error was thrown because the function returned successfully after validation
- Didn't test the complete flow end-to-end

### Lesson Learned
> **A function that validates but doesn't act is incomplete.** Always trace the full flow: input → validation → ACTION → output. If there's no action, the function is just a gatekeeper to nowhere.

### Solution Implemented

**Problem:** Function validated booking data but never saved it. The save code existed but was outside the function (dead code).

**Solution:**
1. Added the missing call to `lead_manager.record_booking()` after validation passes
2. Removed the orphaned dead code that was floating outside the function
3. Added proper error handling and return values

**Result:** Bookings now properly saved to Google Sheets when customers complete the booking flow.

### Prevention
- After writing a handler function, ask: "What does this function actually DO?"
- Test complete user flows, not just individual components
- Look for orphaned code blocks that should be inside functions

---

## Error 4: Missing Data Transformation

### What Happened
Dates and times in Google Sheets were inconsistent - some formal (2025-12-07), some natural language (tomorrow, 3pm, 下午三点).

### Root Cause
The booking system saved whatever the AI extracted from customer messages directly to the sheet without transformation. The AI was instructed to extract in formal format, but didn't always comply.

There was no fallback parsing to ensure consistent format.

### Why I Made This Mistake
- Over-trusted AI to always follow format instructions
- Didn't validate/transform data before saving
- Assumed AI output would be consistent

### Lesson Learned
> **Never trust external input format - including AI output.** Always validate and transform data to the expected format before storing. AI instructions are suggestions, not guarantees.

### Solution Implemented

**Problem:** AI extracted dates/times in various formats ("tomorrow", "3pm", "星期一") and they were saved as-is.

**Solution:**
Created a date/time parser utility (`utils/date_parser.py`) that:
1. Takes natural language date and time strings
2. Recognizes common patterns (English, Chinese, various formats)
3. Converts to canonical format: YYYY-MM-DD for dates, HH:MM for times
4. Falls back to original value if parsing fails (no data loss)

Call this parser before saving to Google Sheets to ensure consistent format.

**Result:** All dates stored as "2025-12-07" format, all times stored as "15:00" format, regardless of how customer expressed them.

### Prevention
- Add parsing/transformation layer between AI extraction and database storage
- Define canonical formats and enforce them in code
- Handle multiple input formats gracefully (natural language, various date formats, etc.)

---

## Summary: Core Principles to Remember

| Principle | Errors Prevented |
|-----------|------------------|
| Prefer bulk API operations over individual cell operations | Error 0 |
| Consider burst limits, not just sustained limits | Error 1 |
| Pass only necessary data to each function | Error 2 |
| Validate that functions perform their intended action | Error 3 |
| Transform and validate all data before storage | Error 4 |
| Test complete flows including restarts and edge cases | Errors 1, 3 |
| Don't trust AI to follow format instructions perfectly | Error 4 |

---

## Quick Checklist for Future Development

- [ ] Am I using bulk operations (`get_all_values`, `update_cells`) instead of individual cell operations?
- [ ] Does this API have burst limits I need to respect?
- [ ] Am I passing unnecessary data (like system prompts) to this function?
- [ ] Does this function actually DO something, or just validate?
- [ ] Am I transforming data to a consistent format before storage?
- [ ] Have I tested the complete user flow end-to-end?
- [ ] Have I tested what happens on service restart?

---

## Related Documentation

| Document | Description |
|----------|-------------|
| `API_QUOTA_ANALYSIS.md` | Full breakdown of quota consumption per feature |
| `SHEET_READ_BREAKDOWN.md` | Which sheets consume most quota per message |
| `README_CACHING_IMPLEMENTATION.md` | How caching was implemented to reduce API calls |
| `CONVERSATION_HISTORY_CACHING.md` | Detailed caching implementation for conversation history |
| `PHASE3_OPTIMIZATION_STATUS.md` | Overall optimization progress and status |
