#!/usr/bin/env python3
"""Fix hybrid menu - simplified direct string replacement"""

file_path = "/root/reflexology-agent(token-optimized)/web/app.py"

with open(file_path) as f:
    lines = f.readlines()

# Backup
with open(file_path + ".backup_v2", "w") as f:
    f.writelines(lines)

print("="*80)
print("IMPLEMENTING HYBRID MENU - LINE BY LINE")
print("="*80)

# Find line numbers
escalation_def_line = None
search_handler_end_line = None
static_menu_line = None
tools_list_line = None
search_booking_handler_line = None

for i, line in enumerate(lines):
    if "def handle_escalation_function_call" in line:
        escalation_def_line = i
    if "return search_result" in line and search_handler_end_line is None:
        search_handler_end_line = i
    if 'menu_config = config.get(\'menu_image\'' in line and static_menu_line is None:
        static_menu_line = i
    if "tools = [" in line and "get_escalation" in lines[i+1]:
        tools_list_line = i
    if 'elif function_name == "search_booking":' in line:
        search_booking_handler_line = i

print(f"Found escalation_def at line {escalation_def_line}")
print(f"Found search_handler_end at line {search_handler_end_line}")
print(f"Found static_menu at line {static_menu_line}")
print(f"Found tools_list at line {tools_list_line}")
print(f"Found search_booking_handler at line {search_booking_handler_line}")

# STEP 1: Insert function definition before escalation handler
func_def = '''

def get_send_menu_image_function_definition():
    """AI function for sending menu"""
    return {
        "type": "function",
        "function": {
            "name": "send_menu_image",
            "description": "Send menu when customer asks about services, treatments, prices",
            "parameters": {
                "type": "object",
                "properties": {
                    "language_preference": {
                        "type": "string",
                        "enum": ["english", "chinese", "auto"]
                    }
                },
                "required": ["language_preference"]
            }
        }
    }

'''

lines.insert(escalation_def_line, func_def)
print("✅ Step 1: Function definition inserted")

# Adjust line numbers
search_handler_end_line += func_def.count('\n')
static_menu_line += func_def.count('\n')
tools_list_line += func_def.count('\n')
search_booking_handler_line += func_def.count('\n')

# STEP 2: Insert handler after search handler
handler_func = '''

def handle_send_menu_image_function_call(fa, phone, wh, cfg, msg):
    """Handle menu sending"""
    logger.info("🖼️  AI menu send")
    lang = fa.get('language_preference', 'auto')
    mc = cfg.get('menu_image', {})
    if not mc.get('enabled'): return {"success": False}
    if lang == 'auto':
        ch = sum(1 for c in msg if u'\\u4e00' <= c <= u'\\u9fff')
        tot = len([c for c in msg if c.strip()])
        lang = 'chinese' if (tot > 0 and ch/tot > 0.3) else 'english'
    url = mc.get('chinese_url' if lang == 'chinese' else 'english_url')
    if not url: return {"success": False}
    try:
        r = wh.send_image(to=phone, image_url=url)
        if r and r.get('sent'):
            logger.info(f"✅ Menu sent ({lang})")
            return {"success": True, "message": "Menu sent"}
        return {"success": False}
    except: return {"success": False}

'''

lines.insert(search_handler_end_line + 1, handler_func)
print("✅ Step 2: Handler inserted")

# Adjust
static_menu_line += handler_func.count('\n')
tools_list_line += handler_func.count('\n')
search_booking_handler_line += handler_func.count('\n')

# STEP 3: Add tracking variable
lines.insert(static_menu_line, "        menu_sent_via_static = False\n        \n")
print("✅ Step 3: Tracking variable added")

# Adjust
tools_list_line += 2
search_booking_handler_line += 2

# STEP 3b: Find "if detect_menu_request" and mark
for i in range(static_menu_line, min(static_menu_line + 50, len(lines))):
    if "if detect_menu_request(user_message, keywords):" in lines[i]:
        lines.insert(i + 1, "                menu_sent_via_static = True\n")
        tools_list_line += 1
        search_booking_handler_line += 1
        # Also change log message
        for j in range(i, min(i + 10, len(lines))):
            if "MENU REQUEST DETECTED" in lines[j]:
                lines[j] = lines[j].replace("MENU REQUEST DETECTED", "STATIC KEYWORD DETECTED")
        break
print("✅ Step 3b: Flag setting added")

# STEP 4: Add to tools list
for i in range(tools_list_line, min(tools_list_line + 10, len(lines))):
    if "get_search_booking_function_definition()" in lines[i]:
        lines.insert(i + 1, "            get_send_menu_image_function_definition(),\n")
        search_booking_handler_line += 1
        break
print("✅ Step 4: Added to tools")

# STEP 5: Add handler case
handler_case = '''
                elif function_name == "send_menu_image":
                    if menu_sent_via_static:
                        menu_result = {"success": True, "message": "Already sent"}
                    else:
                        menu_result = handle_send_menu_image_function_call(
                            function_args, sender, whatsapp_handler, config, user_message)
                    function_results.append({
                        "tool_call_id": tool_call['id'],
                        "role": "tool",
                        "name": function_name,
                        "content": json.dumps(menu_result)
                    })
'''

# Find end of search_booking elif block
for i in range(search_booking_handler_line, min(search_booking_handler_line + 30, len(lines))):
    if "function_results.append" in lines[i] and i > search_booking_handler_line + 5:
        # Find closing })
        for j in range(i, min(i + 10, len(lines))):
            if "})" in lines[j]:
                lines.insert(j + 1, handler_case)
                break
        break
print("✅ Step 5: Handler case added")

# Write
with open(file_path, "w") as f:
    f.writelines(lines)

print("="*80)
print("✅ ALL STEPS DONE!")
print("="*80)
