import os
import shutil
import zipfile
from datetime import datetime

def create_project_backup():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_folder_name = f"學校委員會投票系統_完整備份_{timestamp}"
    backup_dir = os.path.join(os.path.dirname(base_dir), backup_folder_name)
    zip_path = os.path.join(os.path.dirname(base_dir), f"備份_新北市中山國小投票系統_{timestamp}.zip")

    # 1. 複製備份資料夾
    if os.path.exists(backup_dir):
        shutil.rmtree(backup_dir)
    
    shutil.copytree(base_dir, backup_dir, ignore=shutil.ignore_patterns('__pycache__', '.git', '*.pyc', 'excel_dump.json', 'school_roster_dump.json'))
    print(f"Backup folder created at: {backup_dir}")

    # 2. 建立 ZIP 壓縮檔
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(backup_dir):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, backup_dir)
                zipf.write(abs_path, rel_path)

    print(f"Backup zip file created at: {zip_path}")
    return backup_dir, zip_path

if __name__ == '__main__':
    create_project_backup()
