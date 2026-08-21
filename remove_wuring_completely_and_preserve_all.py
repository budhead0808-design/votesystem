from db import get_db, init_db

def process_cleanup():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    # 1. 徹底移除 吳瑞瑛 的被選舉人資格 (從所有投票項目的 candidates 表中移除)
    cursor.execute("SELECT id, committee_id FROM candidates WHERE name LIKE '%吳瑞瑛%'")
    wuring_cands = cursor.fetchall()
    wuring_ids = [c['id'] for c in wuring_cands]

    if wuring_ids:
        placeholders = ','.join(['?'] * len(wuring_ids))
        # 移除 吳瑞瑛 可能存在的個人選票
        cursor.execute(f"DELETE FROM ballots WHERE candidate_id IN ({placeholders})", wuring_ids)
        ballots_deleted = cursor.rowcount
        # 移除 吳瑞瑛 的候選人身分
        cursor.execute(f"DELETE FROM candidates WHERE id IN ({placeholders})", wuring_ids)
        cands_deleted = cursor.rowcount
        print(f"Removed 吳瑞瑛: {cands_deleted} candidate records and {ballots_deleted} ballots deleted.")
    else:
        print("吳瑞瑛 is not present in candidates table.")

    conn.commit()

    # 2. 驗證並保護保留所有其他投票結果與記錄
    cursor.execute("SELECT * FROM ballots")
    all_ballots = [dict(r) for r in cursor.fetchall()]
    cursor.execute("SELECT * FROM voter_logs")
    all_logs = [dict(r) for r in cursor.fetchall()]

    print(f"Preservation verification: Total Ballots in DB={len(all_ballots)}, Total Voter Logs in DB={len(all_logs)}.")
    for b in all_ballots:
        cursor.execute("SELECT name FROM candidates WHERE id = ?", (b['candidate_id'],))
        c_row = cursor.fetchone()
        c_name = c_row['name'] if c_row else 'Unknown'
        print(f" - Preserved Ballot ID #{b['id']}: Committee #{b['committee_id']}, Candidate: {c_name} (Candidate ID: {b['candidate_id']})")

    conn.close()

if __name__ == '__main__':
    process_cleanup()
