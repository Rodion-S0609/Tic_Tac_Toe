import socket
import threading
import db
import random

HOST = '127.0.0.1'
PORT = 5556
clients = {} # Словарь активных соединений {логин: сокет}
waiting_player = None # Переменная для хранения игрока, ищущего матч

# Обработка запросов от конкретного клиента
def client_handler(conn):
    global waiting_player
    current_user = None
    while True:
        try:
            # Получение данных от клиента
            raw_data = conn.recv(1024 * 1000)
            if not raw_data: break
            data = raw_data.decode('utf-8', errors='ignore')
            parts = data.split("|")
            cmd = parts[0]

            # Обработка входа
            if cmd == "LOGIN":
                res = db.login_user(parts[1], parts[2])
                if res and res[2] == 1: # Если пароль верен и юзер не забанен
                    current_user = parts[1]; clients[current_user] = conn
                    role = "ADMIN" if "admin" in current_user.lower() else "USER"
                    conn.send(f"AUTH_OK|{role}|{current_user}|{res[1] or 'None'}".encode())
                else: conn.send("AUTH_ERR".encode())

            # Запрос данных для админки (юзеры и история)
            elif cmd == "GET_USERS":
                users = db.get_all_users()
                u_list = [f"{u[0]},{u[1]},{u[2] if u[2] else 'None'}" for u in users]
                history = db.get_match_history()
                h_list = [f"{h[0]},{h[1]},{h[2]},{h[3]}" for h in history]
                conn.send(f"DATA_UPDATE|{'|'.join(u_list)}# {'|'.join(h_list)}".encode())

            # Действия администратора (бан, кик, удаленное управление)
            elif cmd == "ADMIN_ACTION":
                act, target = parts[1], parts[2]
                if act == "BAN": db.admin_toggle_ban(target)
                if target in clients:
                    msg = f"REMOTE_CMD|{act}"
                    if act == "SEND_FILE": msg += f"|{parts[3]}|{parts[4]}"
                    clients[target].send(msg.encode())
                conn.send("ACTION_OK".encode())

            # Сохранение результата игры в БД
            elif cmd == "GAME_OVER":
                db.record_match(parts[1], parts[2], int(parts[3]))

            # Логика подбора оппонента
            elif cmd == "FIND_GAME":
                if waiting_player is None: waiting_player = (current_user, conn)
                else:
                    # Если есть кто-то в очереди — запускаем игру для двоих
                    opp_n, opp_c = waiting_player; waiting_player = None
                    sym = "X" if random.choice([True, False]) else "O"
                    opp_sym = "O" if sym == "X" else "X"
                    conn.send(f"GAME_START|{sym}|{opp_n}".encode())
                    opp_c.send(f"GAME_START|{opp_sym}|{current_user}".encode())

            # Пересылка хода оппоненту
            elif cmd == "MOVE":
                for u, c in clients.items():
                    if u != current_user: c.send(f"MOVE_UPDATE|{parts[1]}".encode())
        except: break
    
    # Очистка при отключении
    if current_user in clients: del clients[current_user]
    conn.close()

# Запуск сервера
def main():
    db.init_db()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # Повторное использование порта
    s.bind((HOST, PORT)); s.listen(10)
    print("СЕРВЕР ЗАПУЩЕН")
    while True:
        conn, _ = s.accept()
        # Создание нового потока для каждого клиента
        threading.Thread(target=client_handler, args=(conn,), daemon=True).start()

if __name__ == "__main__": main()