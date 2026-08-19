from db import get_db, init_db

def fix_data():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    committee_id = 4

    # 1. 刪除候選人 吳瑞瑛
    cursor.execute("DELETE FROM candidates WHERE committee_id = ? AND name LIKE '%吳瑞瑛%'", (committee_id,))
    deleted_count = cursor.rowcount
    print(f"Deleted 吳瑞瑛 from candidates: {deleted_count} record.")

    # 2. 查出 羅任鎗 的 candidate_id
    cursor.execute("SELECT id, candidate_number, name FROM candidates WHERE committee_id = ? AND name LIKE '%羅任鎗%'", (committee_id,))
    luo_row = cursor.fetchone()

    if luo_row:
        luo_id = luo_row['id']
        # 恢復/寫入 羅任鎗 的投遞選票紀錄 (若無得票則補上 1 票)
        cursor.execute("SELECT COUNT(*) FROM ballots WHERE committee_id = ? AND candidate_id = ?", (committee_id, luo_id))
        vote_count = cursor.fetchone()[0]

        if vote_count == 0:
            cursor.execute("INSERT INTO ballots (committee_id, candidate_id) VALUES (?, ?)", (committee_id, luo_id))
            print(f"Successfully restored 1 vote ballot for 羅任鎗 (Candidate ID: {luo_id}, Number: #{luo_row['candidate_number']})!")
        else:
            print(f"羅任鎗 currently has {vote_count} votes.")

    conn.commit()
    conn.close()

if __name__ == '__main__':
    fix_data()
