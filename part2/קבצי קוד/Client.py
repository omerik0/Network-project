import socket

# הגדרות חיבור - חייבות להתאים לשרת
HOST = '127.0.0.1'
PORT = 65432


def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client_socket.connect((HOST, PORT))
        print("[+] Connected to the bank server.")

        # --- שלב ההזדהות (Login/Register) ---
        username = input("Enter username: ")
        client_socket.send(username.encode('utf-8'))

        # אישור קבלת שם משתמש מהשרת
        server_ack = client_socket.recv(1024).decode('utf-8')

        # בדיקה אם המשתמש קיים או חדש
        status = client_socket.recv(1024).decode('utf-8')

        if status == "EXISTING":
            password = input("Allready registered Enter password: ")
            client_socket.send(password.encode('utf-8'))
        elif status == "NEW":
            password = input("New user! Create a password: ")
            client_socket.send(password.encode('utf-8'))

            # המתנה לבקשת יתרה ראשונית מהשרת
            if client_socket.recv(1024).decode('utf-8') == "BALANCE":
                initial_balance = input("Enter initial deposit amount: ")
                client_socket.send(initial_balance.encode('utf-8'))
        elif status == "ALREADY_CONNECTED":
            print("Error: This user is already logged in from another device.")
            return

        # קבלת אישור סופי לכניסה
        auth_result = client_socket.recv(1024).decode('utf-8')
        print(f"Server response: {auth_result}")

        if "WRONG_PASSWORD" in auth_result:
            print("Access denied. Wrong password.")
            return

        # --- לולאת פקודות ראשית ---
        while True:
            print("\n--- Bank Menu ---")
            print("1: View Balance")
            print("2: Transfer Money")
            print("3: Deposit")
            print("4: Withdraw")
            print("0: Exit")

            choice = input("Select an option: ")

            if choice == '0':
                client_socket.send("0".encode('utf-8'))
                print(client_socket.recv(1024).decode('utf-8'))
                break

            elif choice == '1':
                client_socket.send("1".encode('utf-8'))

            elif choice == '2':
                target = input("Enter target username: ")
                amount = input("Enter amount to transfer: ")
                # הפרוטוקול של השרת שלך מצפה לפורמט -> 2:user:amount
                client_socket.send(f"2:{target}:{amount}".encode('utf-8'))

            elif choice == '3':
                amount = input("Enter amount to deposit: ")
                client_socket.send(f"3:{amount}".encode('utf-8'))

            elif choice == '4':
                amount = input("Enter amount to withdraw: ")
                client_socket.send(f"4:{amount}".encode('utf-8'))

            else:
                print("Invalid choice.")
                continue

            # הדפסת תגובת השרת לפעולה
            response = client_socket.recv(1024).decode('utf-8')
            print(f"\n>>> {response}")

    except ConnectionRefusedError:
        print("[!] Could not connect to the server. Is it running?")
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        client_socket.close()
        print("[-] Connection closed.")


if __name__ == "__main__":
    start_client()