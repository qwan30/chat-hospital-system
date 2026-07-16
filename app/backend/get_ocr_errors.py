import sqlite3

try:
    conn = sqlite3.connect('.local_storage/hospital_ai.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    c.execute("SELECT status, count(*) as c FROM documents GROUP BY status")
    rows = c.fetchall()
    print("Document counts by status:")
    for r in rows:
        print(f"{r['status']}: {r['c']}")
    
    c.execute("SELECT title, status FROM documents LIMIT 20")
    print("\nSample documents:")
    for r in c.fetchall():
        print(f"{r['title']} - {r['status']}")
except Exception as e:
    print(f"Error querying SQLite: {e}")
