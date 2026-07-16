import os, re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if Optional is used but not imported
    if " | None]" in content and "from typing import" in content and "Optional" not in content:
        content = content.replace("from typing import ", "from typing import Optional, ")
    elif " | None]" in content and "from typing import" not in content:
        content = "from typing import Optional\n" + content

    new_content = re.sub(r'Mapped\[([a-zA-Z0-9_\.\[\]]+) \| None\]', r'Mapped[Optional[\1]]', content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for dp, dn, fn in os.walk(r'd:\projects\chatbot-hospital-system\app\backend\src'):
    for f in fn:
        if f.endswith('.py'):
            fix_file(os.path.join(dp, f))
