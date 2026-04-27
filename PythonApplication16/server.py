import socket
import threading
import db
import random

HOST = '127.0.0.1'
PORT = 5556
clients = {}
waiting_player = None # Тут храним того, кто нажал поиск первым

def client_handler(conn):
    global waiting_player
    current_user = None
    
    while True:
        try:
            data = conn.recv(1024 * 1000).decode()
            if not data: break
            parts = data.split("|")
            cmd = parts[0]

            if cmd == "LOGIN":
                res = db.login_user(parts[1], parts[2])
                if res and res[2] == 1:
                    current_user = parts[1]
                    clients[current_user] = conn
                    role = "ADMIN" if "admin" in current_user else "USER"
                    conn.send(f"AUTH_OK|{role}|{current_user}|{res[1] or 'None'}".encode())

            elif cmd == "FIND_GAME":
                if waiting_player is None:
                    # Ты первый в очереди
                    waiting_player = (current_user, conn)
                else:
                    # Нашелся противник!
                    opp_name, opp_conn = waiting_player
                    waiting_player = None
                    
                    # Рандомно решаем, кто Крестик
                    if random.choice([True, False]):
                        conn.send("GAME_START|X".encode())
                        opp_conn.send("GAME_START|O".encode())
                    else:
                        conn.send("GAME_START|O".encode())
                        opp_conn.send("GAME_START|X".encode())

            elif cmd == "MOVE":
                # Пересылаем ход всем остальным (в простом варианте - противнику)
                for u, c in clients.items():
                    if u != current_user:
                        try: c.send(f"MOVE_UPDATE|{parts[1]}".encode())
                        except: pass

            # ... (остальные команды UPDATE_PROFILE, GET_USERS и т.д.)
        except: break
    
    if current_user in clients: del clients[current_user]
    conn.close()

def main():
    db.init_db()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind((HOST, PORT))
    s.listen(10)
    print("SERVER ONLINE")
    while True:
        conn, _ = s.accept()
        threading.Thread(target=client_handler, args=(conn,), daemon=True).start()

if __name__ == "__main__":
    main()