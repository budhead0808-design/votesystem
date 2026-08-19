import openpyxl
import re
from db import init_db, get_db, generate_voter_code

def import_user_excel():
    init_db()
    conn = get_db()
    cursor = conn.cursor()

    excel_path = '特殊優良教師校內初選名單.xlsx'
    wb = openpyxl.load_workbook(excel_path)
    sheet = wb.active

    rows = [[str(c).strip() if c is not None else '' for c in r] for r in sheet.iter_rows(values_only=True) if any(r)]
    
    # 尋找標頭列 (編號, 姓名)
    header_idx = None
    num_col = 0
    name_col = 1
    for idx, r in enumerate(rows):
        if any('姓名' in str(c) for c in r):
            header_idx = idx
            for col_i, cell in enumerate(r):
                if '編號' in cell or '號' in cell:
                    num_col = col_i
                elif '姓名' in cell or '名' in cell:
                    name_col = col_i
            break

    start_row = (header_idx + 1) if header_idx is not None else 0
    candidates = []
    current_num = 1

    for row in rows[start_row:]:
        if not any(row):
            continue
        name = row[name_col] if name_col < len(row) else ''
        if not name or any(k in name for k in ['名單總數', '備註', '初選名單', '說明']):
            continue
        
        num = current_num
        if num_col < len(row):
            try:
                num = int(re.sub(r'\D', '', row[num_col]))
            except:
                num = current_num

        candidates.append({'number': num, 'name': name})
        current_num += 1

    print(f"Extracted {len(candidates)} candidates from {excel_path}.")

    # 1. 建立投票項目
    cursor.execute("""
        INSERT INTO committees (
            title, description, seats_count, alternate_count, max_votes_per_ballot,
            auth_mode, show_gender, show_admin, gender_rule_type, status
        ) VALUES (
            '113學年度 特殊優良教師校內初選票選',
            '匯入自「特殊優良教師校內初選名單.xlsx」，共 82 位候選人。採用免密碼點選姓名領票模式。',
            7, 3, 4, 'direct', 0, 0, 'none', 'active'
        )
    """)
    committee_id = cursor.lastrowid

    # 2. 寫入 82 位候選人與全校教師名冊
    for c in candidates:
        num = c['number']
        name = c['name']
        vcode = generate_voter_code()

        cursor.execute("""
            INSERT INTO candidates (committee_id, candidate_number, name, gender, department, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (committee_id, num, name, '男', '一般', 0))

        cursor.execute("SELECT id FROM teachers WHERE name = ?", (name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO teachers (name, gender, department, is_admin, voter_code) VALUES (?, ?, ?, ?, ?)",
                           (name, '男', '一般', 0, vcode))

    conn.commit()
    conn.close()
    print(f"Successfully imported '{excel_path}' into Committee #{committee_id}!")

if __name__ == '__main__':
    import_user_excel()
