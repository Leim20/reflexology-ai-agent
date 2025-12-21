#!/usr/bin/env python3
"""Fix menu image code to use local file paths instead of URLs"""

# Read the file
with open('web/app.py', 'r') as f:
    content = f.read()

# Replace all inconsistencies
replacements = [
    ('menu_url = menu_config.get(\'chinese_url\')', 'menu_file_path = menu_config.get(\'chinese_file_path\')'),
    ('menu_url = menu_config.get(\'english_url\')', 'menu_file_path = menu_config.get(\'english_file_path\')'),
    ('if not menu_url:', 'if not menu_file_path:'),
    ('logger.warning(f"Menu URL not configured', 'logger.warning(f"Menu file path not configured'),
    ('return {\'success\': False, \'message\': f\'Menu URL not configured', 'return {\'success\': False, \'message\': f\'Menu file path not configured'),
]

for old, new in replacements:
    content = content.replace(old, new)

# Fix filename and mime_type lines
old_filename_block = '''    filename = os.path.basename(urlparse(menu_url).path) or f"menu_{language}"
    mime_type_guess = mimetypes.guess_type(menu_url)[0]
    if "." not in filename:
        ext = mimetypes.guess_extension(mime_type_guess or "image/jpeg") or ".jpg"
        filename = f"{filename}{ext}"
    mime_type = mime_type_guess or "image/jpeg"'''

new_filename_block = '''    filename = f"menu_{language}.png"
    mime_type = "image/png"'''

content = content.replace(old_filename_block, new_filename_block)

# Write back
with open('web/app.py', 'w') as f:
    f.write(content)

print("✅ Code fixed successfully!")
