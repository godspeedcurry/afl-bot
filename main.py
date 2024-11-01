import os  
import time  
import requests  
import sqlite3  
from urllib.parse import quote
from watchdog.observers import Observer  
from watchdog.events import FileSystemEventHandler  
from config import key, target_dir
import urllib.parse  

# 配置Bark推送  

BARK_URL = f"https://api.day.app/{key}/"  


def quote_all_characters(input_string):  
    # 使用 quote 函数对所有字符进行编码，safe='' 表示不保留任何字符  
    return urllib.parse.quote(input_string, safe='')  
# 初始化SQLite数据库，仅创建表一次  
def init_db():  
    conn = sqlite3.connect('crashes.db')  
    cursor = conn.cursor()  
    cursor.execute('''  
        CREATE TABLE IF NOT EXISTS processed_files (  
            id INTEGER PRIMARY KEY AUTOINCREMENT,  
            file_path TEXT UNIQUE  
        )  
    ''')  
    conn.commit()  
    conn.close()  

# 自定义事件处理程序  
class CrashEventHandler(FileSystemEventHandler):  
    def on_created(self, event):  
        # 仅监听文件创建事件  
        if event.is_directory:  
            return  

        file_path = event.src_path  

        # 在此事件处理程序中创建新的数据库连接  
        conn = sqlite3.connect('crashes.db')  
        cursor = conn.cursor()  
        
        try:  
            # 使用 INSERT OR IGNORE 避免重复插入  
            cursor.execute('INSERT OR IGNORE INTO processed_files (file_path) VALUES (?)', (file_path,))  
            if cursor.rowcount > 0:  
                # 唯一插入成功则发送通知  
                print(quote_all_characters(f'Crash found:\n {file_path}我吃'))
                r = requests.get(f"{BARK_URL}" +quote_all_characters(f'Crash found:\n {file_path}') )
                print(r.text)  
            conn.commit()  
        finally:  
            conn.close()  

# 配置监听  
def get_path(target_dir):
    return os.popen(f"find {target_dir} -name 'crashes' -type d").read()

def watch_crash_directories(root_dir=target_dir):  
    init_db()  # 初始化数据库  
    observer = Observer()  

    # 遍历所有out开头的文件夹  
    for crashes_path in get_path(root_dir):  
        event_handler = CrashEventHandler()  
        observer.schedule(event_handler, path=crashes_path, recursive=False)  

    observer.start()  
    try:  
        while True:  
            time.sleep(1)  # 频率可根据需要调整  
    except KeyboardInterrupt:  
        observer.stop()  
    observer.join()  

if __name__ == "__main__":  
    watch_crash_directories()