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
    
    # Only replace UTC with timezone.utc if it's used as a literal UTC
    new_content = re.sub(r'\bUTC\b', 'timezone.utc', new_content)

    # Fix union type anywhere (not just after :)
    # This matches Word | None, e.g. str | None, uuid.UUID | None, int | None, dict[str, Any] | None
    
    # Let's do a simple replace since python regex doesn't support arbitrary nesting
    # We will loop replacing `Type | None` with `Optional[Type]`
    # It might take a few passes for nested ones, but usually it's just `Type | None`.
    
    # Pattern: a python identifier (with optional module prefix and generic brackets) followed by ` | None`
    # E.g. Mapped[str | None], dict[str, Any] | None, list[str] | None
    pattern = re.compile(r'([a-zA-Z_][a-zA-Z0-9_\.]*(?:\[[^\]]*\])?)\s*\|\s*None')
    new_content = pattern.sub(r'Optional[\1]', new_content)

    if new_content != content:
        if 'Optional[' in new_content and 'from typing import' not in new_content:
            new_content = 'from typing import Optional\n' + new_content
        elif 'Optional[' in new_content and 'from typing import Optional' not in new_content:
            new_content = re.sub(r'from typing import (.*)', r'from typing import Optional, \1', new_content, count=1)
        
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
