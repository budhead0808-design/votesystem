import math
from db import get_db

def calculate_election_results(committee_id):
    """
    計算投票結果，動態依據 show_gender 與 show_admin 開關決定是否啟動保障名額與遞補
    """
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM committees WHERE id = ?", (committee_id,))
    committee = cursor.fetchone()
    if not committee:
        conn.close()
        return None

    committee = dict(committee)
    seats_count = committee['seats_count']
    alternate_count = committee['alternate_count']
    show_gender = committee.get('show_gender', 1)
    show_admin = committee.get('show_admin', 1)

    gender_rule_type = committee['gender_rule_type'] if show_gender else 'none'
    min_male = committee['min_male_count'] or 0
    min_female = committee['min_female_count'] or 0
    identity_rule_type = committee['identity_rule_type'] if show_admin else 'none'
    min_non_admin = committee['min_non_admin_count'] or 0

    # 計算性別門檻
    if gender_rule_type == 'one_third':
        required_min_male = math.ceil(seats_count / 3.0)
        required_min_female = math.ceil(seats_count / 3.0)
    elif gender_rule_type == 'half_female':
        required_min_male = 0
        required_min_female = math.ceil(seats_count / 2.0)
    elif gender_rule_type == 'custom':
        required_min_male = min_male
        required_min_female = min_female
    else:
        required_min_male = 0
        required_min_female = 0

    # 計算身分門檻
    if identity_rule_type == 'non_admin_half':
        required_min_non_admin = math.ceil(seats_count / 2.0)
    elif identity_rule_type == 'custom':
        required_min_non_admin = min_non_admin
    else:
        required_min_non_admin = 0

    # 統計得票數
    cursor.execute("""
        SELECT c.*, 
            COALESCE(b.online_votes, 0) + COALESCE(m.manual_votes, 0) AS total_votes
        FROM candidates c
        LEFT JOIN (
            SELECT candidate_id, COUNT(*) as online_votes 
            FROM ballots WHERE committee_id = ? GROUP BY candidate_id
        ) b ON c.id = b.candidate_id
        LEFT JOIN (
            SELECT candidate_id, SUM(votes_count) as manual_votes 
            FROM manual_votes WHERE committee_id = ? GROUP BY candidate_id
        ) m ON c.id = m.candidate_id
        WHERE c.committee_id = ?
        ORDER BY total_votes DESC, c.candidate_number ASC
    """, (committee_id, committee_id, committee_id))
    
    raw_candidates = [dict(row) for row in cursor.fetchall()]
    conn.close()

    logs = []
    logs.append(f"開票作業啟動，總計候選人 {len(raw_candidates)} 位。")
    logs.append(f"應選正取 {seats_count} 人，候補 {alternate_count} 人。")
    
    if show_gender:
        if gender_rule_type == 'one_third':
            logs.append(f"性別規定：任一性別不得少於 1/3 (至少各 {required_min_male} 人)。")
        elif gender_rule_type == 'half_female':
            logs.append(f"性別規定：女性不得少於 1/2 (至少 {required_min_female} 人)。")
        elif gender_rule_type == 'custom':
            logs.append(f"性別規定：自訂限制 (男性至少 {required_min_male} 人，女性至少 {required_min_female} 人)。")
        else:
            logs.append("性別規定：不設限。")
    else:
        logs.append("欄位設定：關閉性別欄位，按得票高低排序。")

    if show_admin and required_min_non_admin > 0:
        logs.append(f"身分規定：未兼行政教師至少 {required_min_non_admin} 人。")

    if not raw_candidates:
        return {
            'committee': committee,
            'winners': [],
            'alternates': [],
            'others': [],
            'logs': logs,
            'tie_cases': []
        }

    candidates = list(raw_candidates)
    
    # 同票偵測
    tie_cases = []
    for i in range(len(candidates) - 1):
        if candidates[i]['total_votes'] == candidates[i+1]['total_votes']:
            if i == seats_count - 1 or i + 1 == seats_count - 1:
                tie_cases.append({
                    'type': '正取邊緣同票',
                    'candidates': [candidates[i], candidates[i+1]],
                    'votes': candidates[i]['total_votes']
                })
            elif i == seats_count + alternate_count - 1 or i + 1 == seats_count + alternate_count - 1:
                tie_cases.append({
                    'type': '候補邊緣同票',
                    'candidates': [candidates[i], candidates[i+1]],
                    'votes': candidates[i]['total_votes']
                })

    winners = candidates[:seats_count]
    unselected = candidates[seats_count:]

    # 性別遞補
    if show_gender:
        def count_gender(cand_list, gender):
            return sum(1 for c in cand_list if c['gender'] == gender)

        def apply_gender_quota(req_gender, min_req):
            nonlocal winners, unselected
            cur_count = count_gender(winners, req_gender)
            if cur_count < min_req:
                shortage = min_req - cur_count
                logs.append(f"⚠️ 性別比例未達標：目前當選正取中【{req_gender}】僅 {cur_count} 人，缺少 {shortage} 人。")
                gender_candidates = [c for c in unselected if c['gender'] == req_gender]
                
                for k in range(min(shortage, len(gender_candidates))):
                    substitute = gender_candidates[k]
                    replaceable_idx = None
                    for idx in range(len(winners) - 1, -1, -1):
                        if winners[idx]['gender'] != req_gender:
                            replaceable_idx = idx
                            break

                    if replaceable_idx is not None:
                        replaced = winners[replaceable_idx]
                        logs.append(f"🔄 啟動性別保障遞補：【{substitute['name']}】({substitute['gender']}，得 {substitute['total_votes']} 票) 遞補正取；替換【{replaced['name']}】(得 {replaced['total_votes']} 票)。")
                        winners[replaceable_idx] = substitute
                        unselected.remove(substitute)
                        unselected.append(replaced)
                        unselected.sort(key=lambda x: (x['total_votes'], -x['candidate_number']), reverse=True)

        if required_min_male > 0:
            apply_gender_quota('男', required_min_male)
        if required_min_female > 0:
            apply_gender_quota('女', required_min_female)

    # 身分遞補
    if show_admin and required_min_non_admin > 0:
        non_admin_count = sum(1 for c in winners if c['is_admin'] == 0)
        if non_admin_count < required_min_non_admin:
            shortage = required_min_non_admin - non_admin_count
            logs.append(f"⚠️ 身分比例未達標：目前正取中【未兼行政教師】僅 {non_admin_count} 人，缺少 {shortage} 人。")
            non_admin_candidates = [c for c in unselected if c['is_admin'] == 0]
            
            for k in range(min(shortage, len(non_admin_candidates))):
                substitute = non_admin_candidates[k]
                replaceable_idx = None
                for idx in range(len(winners) - 1, -1, -1):
                    if winners[idx]['is_admin'] == 1:
                        replaceable_idx = idx
                        break

                if replaceable_idx is not None:
                    replaced = winners[replaceable_idx]
                    logs.append(f"🔄 啟動身分保障遞補：未兼行政【{substitute['name']}】(得 {substitute['total_votes']} 票) 遞補正取；替換【{replaced['name']}】(得 {replaced['total_votes']} 票)。")
                    winners[replaceable_idx] = substitute
                    unselected.remove(substitute)
                    unselected.append(replaced)
                    unselected.sort(key=lambda x: (x['total_votes'], -x['candidate_number']), reverse=True)

    alternates = unselected[:alternate_count]
    others = unselected[alternate_count:]

    logs.append("✅ 最終當選與候補名單計算完成！")

    return {
        'committee': committee,
        'winners': winners,
        'alternates': alternates,
        'others': others,
        'logs': logs,
        'tie_cases': tie_cases
    }
