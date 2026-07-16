import os
import re

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    new_content = content
    
    # Revert datetime.UTC
    new_content = new_content.replace('from datetime import UTC, datetime, timedelta', 'from datetime import datetime, timedelta, timezone')
    new_content = new_content.replace('from datetime import UTC, datetime', 'from datetime import datetime, timezone')
    new_content = new_content.replace('from datetime import datetime, UTC', 'from datetime import datetime, timezone')
    new_content = new_content.replace('from datetime import UTC', 'from datetime import timezone')
    
    # Only replace UTC with timezone.utc if it's used as a literal UTC (not part of another word)
    new_content = re.sub(r'\bUTC\b', 'timezone.utc', new_content)

    # Fix union type
    new_content = re.sub(r':\s*([a-zA-Z0-9_]+(?:\[[^\]]+\])?)\s*\|\s*None', r': Optional[\1]', new_content)
    new_content = re.sub(r'->\s*([a-zA-Z0-9_]+(?:\[[^\]]+\])?)\s*\|\s*None', r'-> Optional[\1]', new_content)

    if 'Optional[' in new_content and 'from typing import' not in new_content:
        new_content = 'from typing import Optional\n' + new_content
    elif 'Optional[' in new_content and 'from typing import Optional' not in new_content:
        new_content = re.sub(r'from typing import (.*)', r'from typing import Optional, \1', new_content, count=1)

    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Fixed {filepath}")

for root, dirs, files in os.walk('src'):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))

for root, dirs, files in os.walk('tests'):
    for file in files:
        if file.endswith('.py'):
            fix_file(os.path.join(root, file))
