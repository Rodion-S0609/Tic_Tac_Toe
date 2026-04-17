import socket
import tkinter as tk
from tkinter import messagebox
from admin import ProfessionalAdminPanel

HOST = '127.0.0.1'
PORT = 5556

class TicTacToeClient:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Terminal Login")
        self.root.geometry("300x250")
        
        self.setup_ui()
        
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(5) 
        try: 
            self.sock.connect((HOST, PORT))
        except Exception as e: 
            messagebox.showerror("Connection Error", f"Сервер спит или порт занят.\nОшибка: {e}")
            self.root.destroy()
            return

        self.root.mainloop()

    def setup_ui(self):
        tk.Label(self.root, text="USER LOGIN", font=("Consolas", 12, "bold")).pack(pady=10)
        
        tk.Label(self.root, text="Email / Node:").pack()
        self.e_ent = tk.Entry(self.root)
        self.e_ent.pack(pady=5)
        
        tk.Label(self.root, text="Password:").pack()
        self.p_ent = tk.Entry(self.root, show="*")
        self.p_ent.pack(pady=5)
        
        tk.Button(self.root, text="AUTHORIZE", bg="#1a1a1a", fg="white", 
                  width=15, command=self.do_login).pack(pady=20)

    def do_login(self):
        login = self.e_ent.get()
        pwd = self.p_ent.get()
        try:
            self.sock.send(f"LOGIN|{login}|{pwd}".encode())
            res = self.sock.recv(1024).decode()
            
            if "AUTH_OK|ADMIN" in res:
                self.root.withdraw()
                ProfessionalAdminPanel(self.sock)
            elif "AUTH_OK|USER" in res:
                messagebox.showinfo("Success", f"Node {login} online!")
            else:
                messagebox.showerror("Denied", "Неверный логин или пароль")
        except:
            messagebox.showerror("Error", "Связь с сервером потеряна")

if __name__ == "__main__":
    TicTacToeClient()