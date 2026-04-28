import socket
import tkinter as tk
from tkinter import messagebox
from admin import ProfessionalAdminPanel
from game import TicTacToeGame

class TicTacToeClient:
    def __init__(self):
        # Окно авторизации
        self.root = tk.Tk()
        self.root.title("Авторизация")
        self.root.geometry("300x250")
        
        # Поля ввода логина и пароля
        tk.Label(self.root, text="ЛОГИН").pack()
        self.u = tk.Entry(self.root); self.u.pack()
        tk.Label(self.root, text="ПАРОЛЬ").pack()
        self.p = tk.Entry(self.root, show="*"); self.p.pack()
        tk.Button(self.root, text="ВОЙТИ", command=self.login).pack(pady=10)
        
        # Создание сокета и подключение к серверу
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try: self.sock.connect(('127.0.0.1', 5556))
        except: 
            messagebox.showerror("Ошибка", "Сервер недоступен")
            self.root.destroy()
        self.root.mainloop()

    # Логика отправки данных на сервер для входа
    def login(self):
        try:
            self.sock.send(f"LOGIN|{self.u.get()}|{self.p.get()}".encode())
            res = self.sock.recv(1024 * 1000).decode().split("|")
            if res[0] == "AUTH_OK":
                role, user, avatar = res[1], res[2], res[3]
                self.root.withdraw() # Прячем окно логина
                # Выбор интерфейса в зависимости от роли
                if role == "ADMIN":
                    ProfessionalAdminPanel(self.sock)
                else: 
                    TicTacToeGame(self.sock, user, avatar)
            else: 
                messagebox.showerror("Ошибка", "Вход запрещен")
        except: 
            messagebox.showerror("Ошибка", "Потеряно соединение")

if __name__ == "__main__":
    TicTacToeClient()