#!/usr/bin/env python3
"""Add search_booking to tools array and tool_calls processing"""
import re

# Read the file
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\web\app.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Step 1: Add to tools array
# Find: get_record_booking_function_definition()
# Replace with: get_record_booking_function_definition(),
#               get_search_booking_function_definition()

pattern1 = r'(get_record_booking_function_definition\(\))(\s*\])'
replacement1 = r'\1,\n            get_search_booking_function_definition()\2'

if re.search(pattern1, content):
    content = re.sub(pattern1, replacement1, content, count=1)
    print('[OK] Step 1: Added search_booking to tools array')
else:
    print('[ERROR] Could not find tools array')
    import sys
    sys.exit(1)

# Step 2: Add handler in tool_calls processing
# Find the record_booking handler and add search_booking after it
pattern2 = r'(elif function_name == "record_booking":.*?function_results\.append\(\{[^}]+\}\))'
match = re.search(pattern2, content, re.DOTALL)

if match:
    new_handler = '''

                elif function_name == "search_booking":
                    search_result = handle_search_booking_function_call(
                        function_args=function_args
                    )

                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(search_result)
                    })'''

    end_pos = match.end()
    content = content[:end_pos] + new_handler + content[end_pos:]
    print('[OK] Step 2: Added search_booking handler to tool_calls processing')
else:
    print('[ERROR] Could not find record_booking handler')
    import sys
    sys.exit(1)

# Write back
with open(r'C:\Users\Hp\Desktop\New folder (2)\reflexology-agent\web\app.py', 'w', encoding='utf-8') as f:
    f.write(content)

print('[OK] All changes applied successfully')
