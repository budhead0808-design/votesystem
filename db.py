import sqlite3
import os
import secrets

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'voting.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    
    # 委員會投票設定表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS committees (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        seats_count INTEGER NOT NULL DEFAULT 5,
        alternate_count INTEGER NOT NULL DEFAULT 0,
        max_votes_per_ballot INTEGER NOT NULL DEFAULT 5,
        auth_mode TEXT NOT NULL DEFAULT 'passcode', 
        -- options: 'direct' (點選姓名領票), 'public' (免驗證自由投), 'passcode' (密碼驗證)
        show_gender INTEGER NOT NULL DEFAULT 1,
        show_admin INTEGER NOT NULL DEFAULT 1,
        gender_rule_type TEXT NOT NULL DEFAULT 'none', 
        min_male_count INTEGER DEFAULT 0,
        min_female_count INTEGER DEFAULT 0,
        identity_rule_type TEXT DEFAULT 'none',
        min_non_admin_count INTEGER DEFAULT 0,
        status TEXT NOT NULL DEFAULT 'active',
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 教師全校名冊表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS teachers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        gender TEXT DEFAULT '男',
        department TEXT DEFAULT '一般',
        is_admin INTEGER DEFAULT 0,
        voter_code TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    # 候選人表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS candidates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER NOT NULL,
        candidate_number INTEGER NOT NULL,
        name TEXT NOT NULL,
        gender TEXT DEFAULT '男',
        department TEXT DEFAULT '一般',
        is_admin INTEGER DEFAULT 0,
        FOREIGN KEY (committee_id) REFERENCES committees (id) ON DELETE CASCADE
    )
    ''')

    # 無記名線上選票投遞表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS ballots (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        vote_time DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (committee_id) REFERENCES committees (id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
    )
    ''')

    # 投票人投票狀態表 (防重複投票)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS voter_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER NOT NULL,
        teacher_id INTEGER NOT NULL,
        voted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(committee_id, teacher_id)
    )
    ''')

    # 實體劃票記錄表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS manual_votes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        committee_id INTEGER NOT NULL,
        candidate_id INTEGER NOT NULL,
        votes_count INTEGER DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (committee_id) REFERENCES committees (id) ON DELETE CASCADE,
        FOREIGN KEY (candidate_id) REFERENCES candidates (id) ON DELETE CASCADE
    )
    ''')

    conn.commit()
    conn.close()

def generate_voter_code(length=6):
    chars = '23456789ABCDEFGHJKLMNPQRSTUVWXYZ'
    return ''.join(secrets.choice(chars) for _ in range(length))

if __name__ == '__main__':
    init_db()
    print("Database schema verified.")
