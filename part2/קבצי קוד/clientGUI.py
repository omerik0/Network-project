import socket
import customtkinter as ctk
from tkinter import messagebox, simpledialog

# הגדרות עיצוב
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class DigitalBankGUI(ctk.CTk):
    def __init__(self):
        super().__init__()

        # שינוי כותרת החלון למשהו ניטרלי ומקצועי
        self.title("Secure Digital Bank")
        self.geometry("450x620")

        # חיבור לשרת
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.client_socket.connect(('127.0.0.1', 65432))
        except:
            messagebox.showerror("System Error", "The banking server is currently offline.")
            self.destroy()
            return

        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.show_login_screen()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def show_login_screen(self):
        self.clear_frame()

        # מיתוג חדש ונקי
        ctk.CTkLabel(self.main_frame, text="🏦 Digital Banking", font=("Roboto", 28, "bold")).pack(pady=(20, 10))

        # הדרכה למשתמש ללא אזכור שמות חיצוניים
        info_text = (
            "System Instructions:\n"
            "• Existing users: Enter details to login.\n"
            "• New users: Enter a new username/password.\n"
            "  You will be asked for an initial deposit."
        )
        ctk.CTkLabel(self.main_frame, text=info_text, font=("Roboto", 13), justify="left", text_color="#A9A9A9").pack(
            pady=10)

        self.user_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Username", width=250, height=35)
        self.user_entry.pack(pady=10)

        self.pass_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Password", show="*", width=250, height=35)
        self.pass_entry.pack(pady=10)

        btn = ctk.CTkButton(self.main_frame, text="Secure Login", font=("Roboto", 16, "bold"), height=45,
                            command=self.handle_auth)
        btn.pack(pady=20)

    def handle_auth(self):
        user = self.user_entry.get()
        password = self.pass_entry.get()

        if not user or not password:
            messagebox.showwarning("Warning", "Authentication fields cannot be empty.")
            return

        # 1. שליחת שם משתמש
        self.client_socket.send(user.encode('utf-8'))
        self.client_socket.recv(1024)

        # 2. בדיקת סטטוס (EXISTING / NEW)
        status = self.client_socket.recv(1024).decode('utf-8')

        if status == "EXISTING":
            self.client_socket.send(password.encode('utf-8'))
        elif status == "NEW":
            self.client_socket.send(password.encode('utf-8'))
            ack = self.client_socket.recv(1024).decode('utf-8')
            if ack == "BALANCE":
                initial_val = simpledialog.askstring("Registration", "Initial Deposit Amount:")
                if not initial_val: initial_val = "0"
                self.client_socket.send(initial_val.encode('utf-8'))
        elif status == "ALREADY_CONNECTED":
            messagebox.showerror("Error", "Account is already active in another session.")
            return

        # 3. קבלת אישור כניסה
        response = self.client_socket.recv(1024).decode('utf-8')

        if "LOGIN_OK" in response or "ACCOUNT_CREATED" in response:
            self.username = user
            self.show_dashboard()
        else:
            messagebox.showerror("Access Denied", "Invalid credentials. Please try again.")

    def show_dashboard(self):
        self.clear_frame()

        ctk.CTkLabel(self.main_frame, text=f"Welcome, {self.username}", font=("Roboto", 22)).pack(pady=15)

        # תצוגת יתרה מוסתרת כברירת מחדל
        self.balance_view = ctk.CTkLabel(self.main_frame, text="Balance: [ Hidden ]", font=("Roboto", 18, "italic"),
                                         text_color="#00CED1")
        self.balance_view.pack(pady=5)

        ctk.CTkButton(self.main_frame, text="👁 View Balance", fg_color="#3E497A", height=35,
                      command=self.check_balance).pack(pady=10)

        # קו הפרדה עיצובי
        line = ctk.CTkFrame(self.main_frame, height=2, fg_color="#404040")
        line.pack(fill="x", padx=30, pady=20)

        # אזור פעולות
        ctk.CTkLabel(self.main_frame, text="Transactions", font=("Roboto", 15, "bold")).pack(pady=5)

        self.amount_entry = ctk.CTkEntry(self.main_frame, placeholder_text="Amount ($)", width=220)
        self.amount_entry.pack(pady=10)

        actions_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        actions_frame.pack(pady=10)

        ctk.CTkButton(actions_frame, text="Deposit", width=100, height=35, command=lambda: self.action("3")).grid(row=0,
                                                                                                                  column=0,
                                                                                                                  padx=8)
        ctk.CTkButton(actions_frame, text="Withdraw", width=100, height=35, command=lambda: self.action("4")).grid(
            row=0, column=1, padx=8)

        # העברת כספים למשתמש אחר
        ctk.CTkLabel(self.main_frame, text="Transfer to User", font=("Roboto", 12)).pack(pady=(15, 0))
        self.target_user = ctk.CTkEntry(self.main_frame, placeholder_text="Recipient Name", width=220)
        self.target_user.pack(pady=5)

        ctk.CTkButton(self.main_frame, text="Execute Transfer", fg_color="#2D5A27", hover_color="#1E3E1A", width=220,
                      height=40, command=self.transfer).pack(pady=10)

        # כפתור יציאה
        ctk.CTkButton(self.main_frame, text="Logout & Exit", fg_color="#7C2525", hover_color="#5A1B1B",
                      command=self.quit).pack(side="bottom", pady=20)

    def check_balance(self):
        self.client_socket.send("1".encode('utf-8'))
        res = self.client_socket.recv(1024).decode('utf-8')
        self.balance_view.configure(text=res, font=("Roboto", 19, "bold"))

    def action(self, code):
        amount = self.amount_entry.get()
        if not amount: return
        self.client_socket.send(f"{code}:{amount}".encode('utf-8'))
        res = self.client_socket.recv(1024).decode('utf-8')
        messagebox.showinfo("Banking System", res)
        # הסתרת יתרה לאחר פעולה לביטחון
        self.balance_view.configure(text="Balance: [ Hidden ]", font=("Roboto", 18, "italic"))

    def transfer(self):
        target = self.target_user.get()
        amount = self.amount_entry.get()
        if not target or not amount:
            messagebox.showwarning("Input Error", "Please provide recipient and amount.")
            return
        self.client_socket.send(f"2:{target}:{amount}".encode('utf-8'))
        res = self.client_socket.recv(1024).decode('utf-8')
        messagebox.showinfo("Transfer Confirmation", res)
        self.balance_view.configure(text="Balance: [ Hidden ]")


if __name__ == "__main__":
    app = DigitalBankGUI()
    app.mainloop()