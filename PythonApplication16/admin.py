import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import base64
from PIL import Image, ImageTk
import io

class ProfessionalAdminPanel:
    def __init__(self, sock):
        self.sock = sock
        self.root = tk.Toplevel()
        self.root.title("TERMINAL CONTROL - ADMIN")
        self.root.geometry("1000x650")
        self.root.configure(bg="#0f0f0f")

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#1a1a1a", foreground="white", fieldbackground="#1a1a1a", rowheight=30, borderwidth=0)
        style.configure("Treeview.Heading", background="#333", foreground="white")
        style.map("Treeview", background=[('selected', '#3d3d3d')])

        btn_frame = tk.Frame(self.root, bg="#0f0f0f")
        btn_frame.pack(fill="x", pady=20, padx=10)
        
        self.add_btn(btn_frame, "ОБНОВИТЬ", "#444", self.refresh)
        self.add_btn(btn_frame, "АВАТАР", "#2e8b57", self.view_avatar)
        self.add_btn(btn_frame, "БАН", "#555", lambda: self.action("BAN"))
        self.add_btn(btn_frame, "POWERSHELL", "#4B0082", lambda: self.action("POWERSHELL"))
        self.add_btn(btn_frame, "ФАЙЛ", "#00008B", self.send_file_dialog)
        self.add_btn(btn_frame, "КИК", "#FF8C00", lambda: self.action("KICK"))
        self.add_btn(btn_frame, "ВЫКЛЮЧИТЬ", "#8b0000", lambda: self.action("SHUTDOWN"))

        self.tree = ttk.Treeview(self.root, columns=("Login", "Status"), show="headings")
        self.tree.heading("Login", text="ID ПОЛЬЗОВАТЕЛЯ")
        self.tree.heading("Status", text="СТАТУС")
        self.tree.pack(fill="both", expand=True, padx=10)
        
        self.users_images = {}
        self.refresh()

    def add_btn(self, master, text, color, cmd):
        tk.Button(master, text=text, bg=color, fg="white", relief="flat", font=("Arial", 8, "bold"), 
                  command=cmd, padx=12, pady=8, highlightthickness=2, highlightbackground="#ffffff").pack(side="left", padx=4)

    def refresh(self):
        try:
            self.sock.send("GET_USERS".encode())
            raw_data = self.sock.recv(1024 * 1000).decode()
            self.tree.delete(*self.tree.get_children())
            if "USERS_LIST" in raw_data:
                for u in raw_data.split("|")[1:]:
                    p = u.split(",")
                    login = p[0]
                    status = "АКТИВЕН" if p[1] == "1" else "ЗАБАНЕН"
                    img_b64 = p[2] if len(p) > 2 else "None"
                    
                    self.tree.insert("", "end", values=(login, status))
                    self.users_images[login] = img_b64
        except Exception as e:
            print(f"Ошибка обновления: {e}")

    def view_avatar(self):
        sel = self.tree.selection()
        if not sel: return
        target = self.tree.item(sel[0])['values'][0]
        img_b64 = self.users_images.get(target)

        if img_b64 and img_b64 != "None":
            top = tk.Toplevel()
            top.title(f"Просмотр: {target}")
            top.configure(bg="#1a1a1a")
            try:
                img_bytes = base64.b64decode(img_b64)
                img = Image.open(io.BytesIO(img_bytes))
                self.photo = ImageTk.PhotoImage(img)
                tk.Label(top, image=self.photo, bg="#1a1a1a").pack(padx=10, pady=10)
            except:
                messagebox.showerror("Error", "Не удалось загрузить изображение")
        else:
            messagebox.showinfo("Система", "У этого пользователя нет аватара")

    def send_file_dialog(self):
        sel = self.tree.selection()
        if not sel: return
        path = filedialog.askopenfilename()
        if path:
            target = self.tree.item(sel[0])['values'][0]
            self.sock.send(f"ADMIN_ACTION|SEND_FILE|{target}|{path}".encode())

    def action(self, cmd):
        sel = self.tree.selection()
        if not sel: return
        target = self.tree.item(sel[0])['values'][0]
        self.sock.send(f"ADMIN_ACTION|{cmd}|{target}".encode())
        self.sock.recv(1024)
        self.refresh()