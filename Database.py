# import sqlite3

# def view_all_data(db_path):
#     conn = sqlite3.connect(db_path)
#     cursor = conn.cursor()

#     # Get list of all tables
#     cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
#     tables = cursor.fetchall()

#     for table_name in tables:
#         table = table_name[0]
#         print(f"\n📄 Table: {table}")
#         print("-" * 40)
        
#         # Get column names
#         cursor.execute(f"PRAGMA table_info({table})")
#         columns = [col[1] for col in cursor.fetchall()]
#         print(" | ".join(columns))

#         # Get all data
#         cursor.execute(f"SELECT * FROM {table}")
#         rows = cursor.fetchall()
#         for row in rows:
#             print(row)

#     conn.close()

# if __name__ == "__main__":
#     view_all_data("database/journal.db")
