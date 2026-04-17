import sqlite3
import hashlib

DB_NAME = 'users.db'

def init_db():
    """Эта функция ОБЯЗАТЕЛЬНО должна быть здесь"""
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        # Создаем таблицу с твоими именами из SSMS
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                          (Id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           Login TEXT UNIQUE, 
                           Password_hash TEXT, 
                           Name TEXT, 
                           Image TEXT, 
                           status INTEGER DEFAULT 1)''')
        
        # Добавляем админа для теста
        admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("INSERT OR IGNORE INTO users (Login, Password_hash, Name, status) VALUES (?, ?, ?, ?)", 
                       ('admin_main_office', admin_pass, 'Main Admin', 1))
        conn.commit()

def login_user(login, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Image, status FROM users WHERE Login=? AND Password_hash=?", (login, hashed))
        return cursor.fetchone()

def get_all_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Login, Password_hash, Image, status FROM users")
        return cursor.fetchall()

def admin_toggle_ban(login):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE users SET status = 1 - status WHERE Login = ?", (login,))

def admin_delete_user(login):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("DELETE FROM users WHERE Login = ?", (login,))