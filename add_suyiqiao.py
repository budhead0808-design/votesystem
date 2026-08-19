from db import get_db, init_db

def add_suyiqiao():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    name = "蘇意喬"
    phone = "0910081574"
    voter_code = "1574"

    # 1. 取得目前進行中的投票項目 ID
    cursor.execute("SELECT id FROM committees WHERE status = 'active' ORDER BY id DESC LIMIT 1")
    c_row = cursor.fetchone()
    if not c_row:
        print("Error: No active committee found!")
        return

    committee_id = c_row['id']

    # 2. 查出目前最大號次
    cursor.execute("SELECT MAX(candidate_number) FROM candidates WHERE committee_id = ?", (committee_id,))
    max_num = cursor.fetchone()[0] or 0
    new_num = max_num + 1

    # 3. 寫入/更新 candidates 表 (候選人名冊)
    cursor.execute("SELECT id FROM candidates WHERE committee_id = ? AND name = ?", (committee_id, name))
    existing_c = cursor.fetchone()

    if existing_c:
        print(f"蘇意喬 is already a candidate in Committee #{committee_id} (ID: {existing_c['id']})")
    else:
        cursor.execute("""
            INSERT INTO candidates (committee_id, candidate_number, name, gender, department, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (committee_id, new_num, name, '女', '一般', 0))
        cand_id = cursor.lastrowid
        print(f"Inserted 蘇意喬 into candidates for Committee #{committee_id} with Candidate Number #{new_num} (ID: {cand_id})")

    # 4. 寫入/更新 teachers 表 (具投票權人，密碼設為 1574)
    cursor.execute("SELECT id FROM teachers WHERE name = ?", (name,))
    existing_t = cursor.fetchone()

    if existing_t:
        cursor.execute("UPDATE teachers SET voter_code = ? WHERE id = ?", (voter_code, existing_t['id']))
        print(f"Updated 蘇意喬 in teachers table (ID: {existing_t['id']}) with passcode: {voter_code}")
    else:
        cursor.execute("INSERT INTO teachers (name, gender, department, is_admin, voter_code) VALUES (?, ?, ?, ?, ?)",
                       (name, '女', '一般', 0, voter_code))
        tid = cursor.lastrowid
        print(f"Inserted 蘇意喬 into teachers table (ID: {tid}) with passcode: {voter_code}")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    add_suyiqiao()
