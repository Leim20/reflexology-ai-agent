# Pending Issues - To Be Fixed Later

## Issue 1: Booking Modification Creates New Row Instead of Updating

**Priority:** Low (not urgent)

**Date Discovered:** 2025-12-28

### Problem:
When user modifies an existing booking (changes date/time), the system creates a NEW row instead of updating the existing booking.

### Example:
- Original booking (Row 6): 2025-12-28, 15:10
- User says: "改去明天晚上8点" (change to tomorrow 8pm)
- Result: NEW Row 7 created (2025-12-29, 20:00), Row 6 unchanged

### Root Cause:
Current UPDATE logic: 
- Different date = treated as new booking

### Additional Issues:
1. Gender becomes "Unknown" when modifying (AI doesn't pass gender)
2. Old booking row remains in sheet (should be removed/updated)

### Proposed Solutions:
| Option | Logic | Behavior |
|--------|-------|----------|
| A) Keep current | Same phone + same date | Different date = new booking |
| B) Update most recent | Find most recent booking for phone | Always update, never duplicate |
| C) Track booking ID | Each booking has unique ID | Modify by ID |

### Files to Modify:
-  -  function
- Prompts - Instruct AI to pass all fields when modifying

---

*This issue is parked for later. Focus on booking reminder first.*
