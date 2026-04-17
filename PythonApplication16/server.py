import socket
import threading
import db
import base64
import os

HOST = '127.0.0.1'
PORT = 5556

def client_handler(conn):
    while True:
        try:
            raw_data = conn.recv(1024 * 500).decode()
            if not raw_data: break
            parts = raw_data.split("|")
            cmd = parts[0]

            if cmd == "LOGIN":
                res = db.login_user(parts[1], parts[2])
                if parts[1] == "admin" and res:
                    conn.send("AUTH_OK|ADMIN".encode())
                elif res:
                    conn.send(f"AUTH_OK|USER|{res[0]}".encode())
                else: conn.send("AUTH_RES:WRONG".encode())

            elif cmd == "GET_USERS":
                users = db.get_all_users()
                data_str = "USERS_LIST|" + "|".join([f"{u[0]},{u[1]},{u[2]},{u[3]}" for u in users])
                conn.send(data_str.encode())

            elif cmd == "ADMIN_ACTION":
                act, target = parts[1], parts[2]
                if act == "BAN": db.admin_toggle_ban(target)
                elif act == "DELETE": db.admin_delete_user(target)
                conn.send("ACTION_OK".encode())
        except: break

def main():
    db.init_db()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(5)
    print(f"Server is running on {PORT}...")
    while True:
        conn, _ = s.accept()
        threading.Thread(target=client_handler, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    main()