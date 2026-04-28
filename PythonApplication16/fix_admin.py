import sqlite3

def unban_admin():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    admin_login = 'admin_main_office' 
    cursor.execute("UPDATE users SET status = 1 WHERE Login = ?", (admin_login,))
    
    if cursor.rowcount > 0:
        print(f"Доступ для {admin_login} успешно восстановлен.")
    else:
        print("Пользователь не найден.")
        
    conn.commit()
    conn.close()

if __name__ == "__main__":
    unban_admin()