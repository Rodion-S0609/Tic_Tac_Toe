import tkinter as tk
from tkinter import ttk, messagebox

class ProfessionalAdminPanel:
    def __init__(self, sock):
        self.sock = sock
        self.root = tk.Toplevel()
        self.root.title("TERMINAL CONTROL - ADMIN")
        self.root.geometry("800x450")
        self.root.configure(bg="#1a1a1a")

        # Кнопки
        btn_frame = tk.Frame(self.root, bg="#1a1a1a")
        btn_frame.pack(fill="x", pady=10)
        
        tk.Button(btn_frame, text="REFRESH", bg="green", fg="white", command=self.refresh).pack(side="left", padx=5)
        tk.Button(btn_frame, text="BAN/UNBAN", bg="purple", fg="white", command=lambda: self.action("BAN")).pack(side="left", padx=5)
        tk.Button(btn_frame, text="DELETE", bg="red", fg="white", command=lambda: self.action("DELETE")).pack(side="left", padx=5)

        # Таблица
        self.tree = ttk.Treeview(self.root, columns=("Email", "Hash", "Status"), show="headings")
        self.tree.heading("Email", text="Email")
        self.tree.heading("Hash", text="Password Hash")
        self.tree.heading("Status", text="Status")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)
        self.refresh()

    def refresh(self):
        self.sock.send("GET_USERS".encode())
        data = self.sock.recv(4096).decode()
        self.tree.delete(*self.tree.get_children())
        if "USERS_LIST" in data:
            for u in data.split("|")[1:]:
                e, h, p, s = u.split(",")
                self.tree.insert("", "end", values=(e, h[:20]+"...", "Active" if s=="1" else "BANNED"))

    def action(self, cmd):
        sel = self.tree.selection()
        if not sel: return
        email = self.tree.item(sel[0])['values'][0]
        self.sock.send(f"ADMIN_ACTION|{cmd}|{email}".encode())
        self.sock.recv(1024)
        self.refresh()