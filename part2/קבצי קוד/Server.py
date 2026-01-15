import socket
import threading
import pickle

HOST = '127.0.0.1'
PORT = 65432

clients = {}       # {username: socket} – כרגע מחוברים
balances = {}      # {username: balance}
passwords = {}     # {username: password}
lock = threading.Lock()


def save_data():
    """Save balances and passwords to file"""
    with open('bank_data.pkl', 'wb') as f:
        pickle.dump({'balances': balances, 'passwords': passwords}, f)


def load_data():
    """Load balances and passwords if exists"""
    global balances, passwords
    try:
        with open('bank_data.pkl', 'rb') as f:
            data = pickle.load(f)
            balances = data.get('balances', {})
            passwords = data.get('passwords', {})
    except FileNotFoundError:
        balances = {}
        passwords = {}


def handle_client(client_socket, address):
    username = None
    try:
        while True:
            username = client_socket.recv(1024).decode('utf-8')
            client_socket.send("USERNAME_RECEIVED".encode('utf-8'))

            with lock:
                if username in clients:
                    # User already connected
                    client_socket.send("ALREADY_CONNECTED".encode('utf-8'))
                    continue

                if username in passwords:
                    # Existing user: ask for password
                    client_socket.send("EXISTING".encode('utf-8'))
                    password = client_socket.recv(1024).decode('utf-8')
                    if password != passwords[username]:
                        client_socket.send("WRONG_PASSWORD".encode('utf-8'))
                        continue
                    else:

                        client_socket.send("LOGIN_OK".encode('utf-8'))
                        break
                else:
                    # New user: ask for password
                    client_socket.send("NEW".encode('utf-8'))
                    password = client_socket.recv(1024).decode('utf-8')
                    passwords[username] = password

                    # Ask for initial balance
                    client_socket.send("BALANCE".encode('utf-8'))
                    initial_balance = float(client_socket.recv(1024).decode('utf-8'))
                    balances[username] = initial_balance
                    client_socket.send(f"ACCOUNT_CREATED:{initial_balance}".encode('utf-8'))
                    break

        clients[username] = client_socket
        print(f"[+] {username} connected from {address}")

        while True:
            data = client_socket.recv(1024).decode('utf-8')
            if not data:
                break

            command = data.split(':')
            action = command[0]

            with lock:
                if action == '0':  # Disconnect
                    client_socket.send("Disconnected.".encode('utf-8'))
                    break

                elif action == '1':  # View balance
                    client_socket.send(f"Your balance: {balances[username]:.2f}".encode('utf-8'))

                elif action == '2':  # Transfer
                    target_user = command[1]
                    amount = float(command[2])
                    if target_user not in balances:
                        client_socket.send(f"Error: User {target_user} not found.".encode('utf-8'))
                    elif amount > balances[username]:
                        client_socket.send("Error: Insufficient funds.".encode('utf-8'))
                    else:
                        balances[username] -= amount
                        balances[target_user] += amount
                        client_socket.send(f"Transferred {amount:.2f} to {target_user}".encode('utf-8'))

                elif action == '3':  # Deposit
                    amount = float(command[1])
                    balances[username] += amount
                    client_socket.send(f"Deposited {amount:.2f}. New balance: {balances[username]:.2f}".encode('utf-8'))

                elif action == '4':  # Withdraw
                    amount = float(command[1])
                    if amount > balances[username]:
                        client_socket.send("Error: Insufficient funds.".encode('utf-8'))
                    else:
                        balances[username] -= amount
                        client_socket.send(f"Withdrew {amount:.2f}. New balance: {balances[username]:.2f}".encode('utf-8'))

        save_data()

    except Exception as e:
        print(f"[!] Error handling client {username}: {e}")
    finally:
        with lock:
            if username in clients:
                del clients[username]
        client_socket.close()
        print(f"[-] Connection with {username} closed.")


def start_server():
    load_data()
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen(5)
    print(f"[*] Bank server listening on {HOST}:{PORT}")

    while True:
        conn, addr = server.accept()
        thread = threading.Thread(target=handle_client, args=(conn, addr))
        thread.start()


if __name__ == "__main__":
    start_server()