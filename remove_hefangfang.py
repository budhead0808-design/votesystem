from db import get_db, init_db

def remove_person():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM candidates WHERE name LIKE '%何芳芳%'")
    cand_deleted = cursor.rowcount

    cursor.execute("DELETE FROM teachers WHERE name LIKE '%何芳芳%'")
    teacher_deleted = cursor.rowcount

    conn.commit()
    conn.close()

    print(f"Successfully deleted 何芳芳: {cand_deleted} candidate records and {teacher_deleted} teacher records removed.")

if __name__ == '__main__':
    remove_person()
