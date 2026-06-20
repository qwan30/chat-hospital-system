import os
import re

def replace_in_file(path):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Regex to find X | None
    new_content = re.sub(r'([A-Za-z0-9_\[\]\.]+) \| None', r'Optional[\1]', content)

    if new_content != content:
        # Check if typing import exists
        if 'from typing import ' in new_content:
            if 'Optional' not in new_content:
                new_content = new_content.replace('from typing import ', 'from typing import Optional, ', 1)
        else:
            # add import typing at top after from __future__
            if 'from __future__ import annotations' in new_content:
                new_content = new_content.replace('from __future__ import annotations\n', 'from __future__ import annotations\nfrom typing import Optional\n')
            else:
                new_content = 'from typing import Optional\n' + new_content

        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {path}")

for root, dirs, files in os.walk('src/hospital_ai'):
    for file in files:
        if file.endswith('.py'):
            replace_in_file(os.path.join(root, file))
