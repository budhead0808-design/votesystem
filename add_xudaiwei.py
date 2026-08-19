from db import get_db, init_db

def add_xudaiwei():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    name = "徐岱瑋"
    phone = "0930432218"
    voter_code = "2218"

    # 1. 確保徐岱瑋不在 candidates (非候選人)
    cursor.execute("DELETE FROM candidates WHERE name LIKE '%徐岱瑋%'")
    cand_deleted = cursor.rowcount

    # 2. 檢查或新增/更新至 teachers (具投票權人)
    cursor.execute("SELECT id FROM teachers WHERE name LIKE '%徐岱瑋%'")
    existing = cursor.fetchone()

    if existing:
        cursor.execute("UPDATE teachers SET voter_code = ?, is_admin = 1 WHERE id = ?", (voter_code, existing['id']))
        print(f"Updated 徐岱瑋 in teachers table (ID: {existing['id']}) with passcode: {voter_code}")
    else:
        cursor.execute("INSERT INTO teachers (name, gender, department, is_admin, voter_code) VALUES (?, ?, ?, ?, ?)",
                       (name, '女', '一般', 1, voter_code))
        tid = cursor.lastrowid
        print(f"Inserted 徐岱瑋 into teachers table (ID: {tid}) with passcode: {voter_code}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_xudaiwei()
