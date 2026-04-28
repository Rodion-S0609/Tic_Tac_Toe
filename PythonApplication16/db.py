import sqlite3
import hashlib
from datetime import datetime

DB_NAME = 'users.db'

def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                          (Id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           Login TEXT UNIQUE, 
                           Password_hash TEXT, 
                           Image TEXT, 
                           status INTEGER DEFAULT 1)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS matches 
                          (Id INTEGER PRIMARY KEY AUTOINCREMENT, 
                           Winner TEXT, 
                           Loser TEXT, 
                           Draw INTEGER DEFAULT 0,
                           Timestamp DATETIME)''')
        
        admin_pass = hashlib.sha256('admin123'.encode()).hexdigest()
        cursor.execute("INSERT OR IGNORE INTO users (Login, Password_hash, status) VALUES (?, ?, ?)", 
                       ('admin_main_office', admin_pass, 1))
        conn.commit()

def login_user(login, password):
    hashed = hashlib.sha256(password.encode()).hexdigest()
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Login, Image, status FROM users WHERE Login=? AND Password_hash=?", (login, hashed))
        return cursor.fetchone()

def update_profile(old_login, new_login, img_base64):
    with sqlite3.connect(DB_NAME) as conn:
        if img_base64:
            conn.execute("UPDATE users SET Login = ?, Image = ? WHERE Login = ?", (new_login, img_base64, old_login))
        else:
            conn.execute("UPDATE users SET Login = ? WHERE Login = ?", (new_login, old_login))
        conn.commit()

def get_all_users():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Login, status, Image FROM users")
        return cursor.fetchall()

def admin_toggle_ban(login):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("UPDATE users SET status = 1 - status WHERE Login = ?", (login,))

def record_match(winner, loser, is_draw=0):
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("INSERT INTO matches (Winner, Loser, Draw, Timestamp) VALUES (?, ?, ?, ?)",
                     (winner, loser, is_draw, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        conn.commit()

def get_match_history():
    with sqlite3.connect(DB_NAME) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT Winner, Loser, Draw, Timestamp FROM matches ORDER BY Id DESC")
        return cursor.fetchall()