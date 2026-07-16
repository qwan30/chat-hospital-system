import json
import subprocess

result = subprocess.run(
    ["gh", "pr", "list", "--author", "qwan30", "--state", "open", "--json", "number,title,mergeable,statusCheckRollup"],
    capture_output=True,
    text=True,
    encoding="utf-8"
)

try:
    data = json.loads(result.stdout)
    for p in data:
        status_checks = p.get('statusCheckRollup') or []
        failed = [c['name'] for c in status_checks if c.get('conclusion') == 'FAILURE']
        print(f"PR {p['number']}: {p['title']}")
        print(f"  Mergeable: {p['mergeable']}")
        print(f"  Failed Checks: {failed}")
except Exception as e:
    print(f"Error parsing JSON: {e}")
    print("Raw stdout:")
    print(result.stdout)
