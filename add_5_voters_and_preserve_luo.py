import re
from db import get_db, init_db

def process_updates():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    committee_id = 4

    # 1. 確保並保留 羅任鎗 的投票結果與領票紀錄
    cursor.execute("SELECT id, candidate_number, name FROM candidates WHERE committee_id = ? AND name LIKE '%羅任鎗%'", (committee_id,))
    luo_cand = cursor.fetchone()
    if luo_cand:
        luo_cand_id = luo_cand['id']
        cursor.execute("SELECT COUNT(*) FROM ballots WHERE committee_id = ? AND candidate_id = ?", (committee_id, luo_cand_id))
        ballot_count = cursor.fetchone()[0]
        if ballot_count == 0:
            cursor.execute("INSERT INTO ballots (committee_id, candidate_id) VALUES (?, ?)", (committee_id, luo_cand_id))
            print(f"Preserved & inserted 1 ballot for 羅任鎗 (Candidate ID: {luo_cand_id}).")

    cursor.execute("SELECT id, name FROM teachers WHERE name LIKE '%羅任鎗%'")
    luo_teacher = cursor.fetchone()
    if luo_teacher:
        luo_teacher_id = luo_teacher['id']
        cursor.execute("SELECT COUNT(*) FROM voter_logs WHERE committee_id = ? AND (teacher_id = ? OR teacher_name = ?)", (committee_id, luo_teacher_id, '羅任鎗'))
        log_count = cursor.fetchone()[0]
        if log_count == 0:
            cursor.execute("INSERT INTO voter_logs (committee_id, teacher_id, teacher_name) VALUES (?, ?, ?)", (committee_id, luo_teacher_id, '羅任鎗'))
            print(f"Recorded voter_logs for 羅任鎗 (Teacher ID: {luo_teacher_id}).")

    # 2. 加入/更新 5 位有投票權但非候選人的老師名單與手機末4碼密碼
    voters = [
        {'name': '彭筠軫', 'code': '7730', 'is_admin': 0},
        {'name': '吳嘉羚', 'code': '9239', 'is_admin': 0},
        {'name': '馮于芷', 'code': '9623', 'is_admin': 1},
        {'name': '郭映廷', 'code': '8871', 'is_admin': 1},
        {'name': '陳嫝誼', 'code': '0809', 'is_admin': 0}
    ]

    for v in voters:
        name = v['name']
        code = v['code']
        is_admin = v['is_admin']

        # 確保非候選人 (從 candidates 中移除)
        cursor.execute("DELETE FROM candidates WHERE committee_id = ? AND name LIKE ?", (committee_id, f"%{name}%"))

        # 新增/更新至 teachers 投票權人名冊
        cursor.execute("SELECT id FROM teachers WHERE name LIKE ?", (f"%{name}%",))
        existing_t = cursor.fetchone()
        if existing_t:
            cursor.execute("UPDATE teachers SET voter_code = ?, is_admin = ? WHERE id = ?", (code, is_admin, existing_t['id']))
            print(f"Updated teacher {name} (ID: {existing_t['id']}) passcode -> {code}")
        else:
            cursor.execute("INSERT INTO teachers (name, gender, department, is_admin, voter_code) VALUES (?, ?, ?, ?, ?)",
                           (name, '女', '一般', is_admin, code))
            tid = cursor.lastrowid
            print(f"Inserted new teacher {name} (ID: {tid}) passcode -> {code}")

    conn.commit()

    # 驗證統計
    cursor.execute("SELECT COUNT(*) FROM ballots WHERE committee_id = ?", (committee_id,))
    total_ballots = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM voter_logs WHERE committee_id = ?", (committee_id,))
    total_logs = cursor.fetchone()[0]

    print(f"Verification complete: Committee #{committee_id} Total Ballots={total_ballots}, Total Voter Logs={total_logs}.")
    conn.close()

if __name__ == '__main__':
    process_updates()
