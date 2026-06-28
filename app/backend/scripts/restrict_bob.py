import sqlite3

conn = sqlite3.connect(".local_storage/hospital_ai.db")
cursor = conn.cursor()

# Delete nurse permission for Bob (p-002)
cursor.execute("""
    DELETE FROM patient_permissions 
    WHERE user_id = '10000000000000000000000000000005' 
      AND patient_id = '20000000000000000000000000000002'
""")
conn.commit()
print("Nurse permissions for Bob deleted. Total rows changed:", conn.total_changes)

# Also check what permissions are left for nurse on p-002
cursor.execute("""
    SELECT COUNT(*) FROM patient_permissions 
    WHERE user_id = '10000000000000000000000000000005' 
      AND patient_id = '20000000000000000000000000000002'
""")
print("Remaining permissions for nurse on Bob:", cursor.fetchone()[0])
conn.close()
