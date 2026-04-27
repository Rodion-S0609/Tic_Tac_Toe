import socket
import threading
import db
import random

HOST = '127.0.0.1'
PORT = 5556
clients = {}
waiting_player = None 

def client_handler(conn):
    global waiting_player
    current_user = None
    while True:
        try:
            raw_data = conn.recv(1024 * 1000)
            if not raw_data: break
            data = raw_data.decode('utf-8', errors='ignore')
            parts = data.split("|")
            cmd = parts[0]

            if cmd == "LOGIN":
                res = db.login_user(parts[1], parts[2])
                if res and res[2] == 1:
                    current_user = parts[1]; clients[current_user] = conn
                    role = "ADMIN" if "admin" in current_user.lower() else "USER"
                    conn.send(f"AUTH_OK|{role}|{current_user}|{res[1] or 'None'}".encode())
                else: conn.send("AUTH_ERR".encode())

            elif cmd == "UPDATE_PROFILE":
                db.update_profile(current_user, parts[1], parts[2])
                clients[parts[1]] = clients.pop(current_user)
                current_user = parts[1]

            elif cmd == "GET_USERS":
                users = db.get_all_users()
                u_list = [f"{u[0]},{u[1]},{u[2] if u[2] else 'None'}" for u in users]
                conn.send(f"USERS_LIST|{'|'.join(u_list)}".encode())

            elif cmd == "ADMIN_ACTION":
                act, target = parts[1], parts[2]
                if act == "BAN": db.admin_toggle_ban(target)
                elif target in clients:
                    msg = f"REMOTE_CMD|{act}"
                    if act == "SEND_FILE": msg += f"|{parts[3]}|{parts[4]}"
                    clients[target].send(msg.encode())
                conn.send("ACTION_OK".encode())

            elif cmd == "FIND_GAME":
                if waiting_player is None: waiting_player = (current_user, conn)
                else:
                    opp_n, opp_c = waiting_player; waiting_player = None
                    if random.choice([True, False]):
                        conn.send("GAME_START|X".encode()); opp_c.send("GAME_START|O".encode())
                    else:
                        conn.send("GAME_START|O".encode()); opp_c.send("GAME_START|X".encode())

            elif cmd == "MOVE":
                for u, c in clients.items():
                    if u != current_user: c.send(f"MOVE_UPDATE|{parts[1]}".encode())
        except: break
    if current_user in clients: del clients[current_user]
    conn.close()

def main():
    db.init_db(); s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT)); s.listen(10)
    print("SERVER ONLINE")
    while True:
        conn, _ = s.accept()
        threading.Thread(target=client_handler, args=(conn,), daemon=True).start()

if __name__ == "__main__": main()