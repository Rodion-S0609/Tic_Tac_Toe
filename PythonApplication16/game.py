import tkinter as tk
from tkinter import messagebox, filedialog
import base64
import threading
import io
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

        tk.Button(self.root, text="НАСТРОЙКИ ПРОФИЛЯ", bg="#333", fg="white", 
                  relief="flat", command=self.edit_profile).pack(pady=5)
        
        self.btn_search = tk.Button(self.root, text="ПОИСК ИГРЫ", bg="#4b6eaf", fg="white", 
                                   font=("Arial", 11, "bold"), command=self.start_search)
        self.btn_search.pack(pady=10, fill="x", padx=50)

        # Игровое поле
        self.grid_frame = tk.Frame(self.root, bg="#1a1a1a")
        self.grid_frame.pack()
        self.btns = []
        for i in range(9):
            b = tk.Button(self.grid_frame, text="", font=("Arial", 20, "bold"), width=4, height=2, 
                          bg="#262626", fg="white", command=lambda idx=i: self.click(idx))
            b.grid(row=i//3, column=i%3, padx=2, pady=2)
            self.btns.append(b)

        self.status_label = tk.Label(self.root, text="Система готова", fg="gray", bg="#1a1a1a")
        self.status_label.pack(pady=10)

    def update_avatar_ui(self, b64):
        if b64 and b64 != "None":
            try:
                img_data = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_data))
                img = img.resize((80, 80), Image.Resampling.LANCZOS)
                self.photo = ImageTk.PhotoImage(img)
                self.avatar_label.config(image=self.photo)
            except Exception as e:
                print(f"Ошибка отрисовки аватара: {e}")

    def edit_profile(self):
        edit_win = tk.Toplevel(self.root)
        edit_win.title("Настройки профиля")
        edit_win.geometry("300x250")
        edit_win.configure(bg="#2b2b2b")
        
        tk.Label(edit_win, text="Новый ник:", fg="white", bg="#2b2b2b").pack(pady=5)
        new_nick_ent = tk.Entry(edit_win)
        new_nick_ent.insert(0, self.login)
        new_nick_ent.pack(pady=5)

        self.temp_b64 = self.avatar_b64

        def select_file():
            path = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp *.psd")])
            if path:
                try:
                    img = Image.open(path).convert("RGB")
                    img.thumbnail((150, 150))
                    buf = io.BytesIO()
                    img.save(buf, format="JPEG")
                    self.temp_b64 = base64.b64encode(buf.getvalue()).decode()
                    messagebox.showinfo("Успех", "Изображение загружено!")
                except Exception as e:
                    messagebox.showerror("Ошибка", f"Не удалось прочитать файл: {e}")

        tk.Button(edit_win, text="ВЫБРАТЬ ФОТО", command=select_file, bg="#444", fg="white").pack(pady=10)
        
        def save():
            new_name = new_nick_ent.get()
            if new_name:
                self.sock.send(f"UPDATE_PROFILE|{new_name}|{self.temp_b64}".encode())
                self.login = new_name
                self.avatar_b64 = self.temp_b64
                self.name_label.config(text=self.login)
                self.update_avatar_ui(self.avatar_b64)
                edit_win.destroy()
                messagebox.showinfo("Обновление", "Профиль успешно изменен!")

        tk.Button(edit_win, text="СОХРАНИТЬ", command=save, bg="#2e8b57", fg="white").pack(pady=10)

    def check_winner(self):
        win_coords = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        for a, b, c in win_coords:
            if self.btns[a]['text'] == self.btns[b]['text'] == self.btns[c]['text'] != "":
                winner_sym = self.btns[a]['text']
                self.game_active = False
                if winner_sym == self.symbol:
                    messagebox.showinfo("ФИНАЛ", "ПОБЕДА! Вы разнесли противника.")
                else:
                    messagebox.showinfo("ФИНАЛ", "ПОРАЖЕНИЕ. Попробуйте еще раз.")
                self.reset_grid()
                return True
        
        if all(b['text'] != "" for b in self.btns):
            messagebox.showinfo("ФИНАЛ", "НИЧЬЯ! Свободных клеток нет.")
            self.reset_grid()
            return True
        return False

    def reset_grid(self):
        for b in self.btns:
            b.config(text="", state="normal")
        self.btn_search.config(state="normal", text="ПОИСК ИГРЫ")
        self.status_label.config(text="Игра окончена")

    def start_search(self):
        try:
            self.sock.send("FIND_GAME".encode())
            self.btn_search.config(state="disabled", text="ПОИСК...")
            self.status_label.config(text="Ищем достойного оппонента...")
        except:
            messagebox.showerror("Ошибка", "Потеряно соединение с сервером")

    def click(self, idx):
        if self.my_turn and self.game_active and self.btns[idx]['text'] == "":
            self.btns[idx].config(text=self.symbol, fg="#00FF00")
            self.sock.send(f"MOVE|{idx}".encode())
            self.my_turn = False
            self.check_winner()

    def receiver(self):
        while True:
            try:
                raw_data = self.sock.recv(1024 * 1000)
                if not raw_data: break
                data = raw_data.decode()
                p = data.split("|")
                
                if p[0] == "GAME_START":
                    self.symbol = p[1]
                    self.game_active = True
                    self.my_turn = (self.symbol == "X")
                    self.status_label.config(text=f"БИТВА! Вы играете за: {self.symbol}")
                    for b in self.btns: b.config(text="")
                
                elif p[0] == "MOVE_UPDATE":
                    idx = int(p[1])
                    opp_sym = "O" if self.symbol == "X" else "X"
                    self.btns[idx].config(text=opp_sym, fg="#FF4444")
                    self.my_turn = True
                    self.check_winner()
            except:
                break