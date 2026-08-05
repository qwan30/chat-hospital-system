import os


def process_file(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()

    changed = False

    if "EntityRelationExtractor:  =" in content:
        content = content.replace("EntityRelationExtractor:  =", "EntityRelationExtractor =")
        changed = True

    if "from __future__ import annotations\n" in content:
        content = content.replace("from __future__ import annotations\n", "")

        insert_idx = 0
        if content.startswith('"""'):
            end_idx = content.find('"""', 3)
            if end_idx != -1:
                insert_idx = content.find("\n", end_idx) + 1
        elif content.startswith("'''"):
            end_idx = content.find("'''", 3)
            if end_idx != -1:
                insert_idx = content.find("\n", end_idx) + 1

        content = content[:insert_idx] + "from __future__ import annotations\n" + content[insert_idx:]
        changed = True

    if changed:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)


for root, _, files in os.walk("src"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))

for root, _, files in os.walk("tests"):
    for file in files:
        if file.endswith(".py"):
            process_file(os.path.join(root, file))
