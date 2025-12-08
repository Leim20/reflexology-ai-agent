#!/usr/bin/env python3
"""Fix template validation to recognize pre-filled fields"""
import re

# New STEP 2 section with pre-filled field handling
new_section = '''## STEP 2: After Customer Fills and Sends Back Template

Customer will send you a message with filled information. Extract all details:
- Name (姓名/Name)
- Gender (性别/Gender) - Important for policy enforcement!
- Phone (电话/Phone)
- Date (日期/Date)
- Time (时间/Time)
- Service (服务/Service)
- Therapist preference (女技师/男技师)

**Recognition patterns for Gender:**
- "女" / "女生" / "Female" / "F" / "girl" / "woman"
- "男" / "男生" / "Male" / "M" / "boy" / "man"

**🚨 IMPORTANT - Handling Pre-filled Template Fields:**

⚠️ If you sent a template with ANY field already pre-filled (e.g., service = "120分钟香薰疗法"):
- Check if customer's response includes that field
- If customer does NOT mention it → They ACCEPTED the pre-filled value!
- DO NOT ask for it again!
- Only validate fields that were EMPTY in the template you sent

**Example:**
You sent template with:
- "按摩服务 & 时长：120分钟香薰身体按摩" ← PRE-FILLED
- Other fields: empty

Customer responds: "wjj,女，60987654321, 明天下午五点半，女技师"

✅ CORRECT validation:
- Name: wjj ✓
- Gender: 女 ✓
- Phone: 60987654321 ✓
- Date: 明天 ✓
- Time: 下午五点半 ✓
- Service: 120分钟香薰身体按摩 ✓ (accepted pre-filled value)
- Therapist: 女技师 ✓

❌ WRONG: Don't ask "还需要您的按摩服务和时长哦😊" because it was already provided!

**Validation Checklist (Check ONLY fields that were EMPTY in your template):**
☐ Did customer provide name? (if template name field was empty)
☐ Did customer provide gender? (if template gender field was empty)
☐ Did customer provide phone? (if template phone field was empty)
☐ Did customer provide date? (if template date field was empty)
☐ Did customer provide time? (if template time field was empty)
☐ Did customer provide service type? (if template service field was empty)
☐ Did customer provide therapist preference? (if template therapist field was empty)

If ANY **originally empty** field is still missing → Ask: "还需要您的[missing field]哦😊"

⚠️ If ALL fields are complete (including pre-filled ones) → Proceed to STEP 2.5 for policy check
'''

# Read the prompts file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Find and replace STEP 2: After Customer Fills and Sends Back Template
# Pattern: from "## STEP 2: After Customer" to just before "## STEP 2.5:"
pattern = r'## STEP 2: After Customer Fills and Sends Back Template.*?(?=## STEP 2\.5:)'

if re.search(pattern, content, re.DOTALL):
    content = re.sub(pattern, new_section + '\n\n', content, flags=re.DOTALL)
    print('[OK] Updated STEP 2 validation with pre-filled field handling')
else:
    print('[ERROR] Could not find STEP 2 section')
    import sys
    sys.exit(1)

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\config\prompts\whatsapp_with_knowledge.txt', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] Prompts file updated successfully')
