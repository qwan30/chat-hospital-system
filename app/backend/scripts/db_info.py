import sqlite3
import os

db_path = ".local_storage/hospital_ai.db"
if not os.path.exists(db_path):
    print("Database path not found")
else:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print("Tables:", tables)
    for table_name_tuple in tables:
        table_name = table_name_tuple[0]
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            cnt = cursor.fetchone()[0]
            print(f"  {table_name}: {cnt} rows")
            if table_name == "patients" or "patient" in table_name:
                cursor.execute(f"SELECT id, full_name, mrn FROM {table_name}")
                print(f"    Rows in {table_name}:", cursor.fetchall())
        except Exception as e:
            print(f"  Error on {table_name}: {e}")
    conn.close()
