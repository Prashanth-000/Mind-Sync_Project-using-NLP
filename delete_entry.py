# import sqlite3
# import os

# def delete_entry_and_tasks(entry_id, db_path='database/journal.db'):
#     if not os.path.exists(db_path):
#         print("Database file not found.")
#         return

#     try:
#         conn = sqlite3.connect(db_path)
#         cursor = conn.cursor()

#         # Check if the entry exists
#         cursor.execute("SELECT * FROM entries WHERE id = ?", (entry_id,))
#         entry = cursor.fetchone()
#         if not entry:
#             print(f"No entry found with ID {entry_id}")
#             return

#         # Delete associated tasks first
#         cursor.execute("DELETE FROM tasks WHERE entry_id = ?", (entry_id,))

#         # Then delete the entry
#         cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))

#         conn.commit()
#         print(f"Entry (ID {entry_id}) and its tasks deleted successfully.")

#     except sqlite3.Error as e:
#         print("SQLite error:", e)

#     finally:
#         conn.close()

# # Example usage
# if __name__ == "__main__":
#     entry_id_to_delete = int(input("Enter the entry ID to delete: "))
#     delete_entry_and_tasks(entry_id_to_delete)
