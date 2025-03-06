import socket
import threading

# Use 0.0.0.0 to listen on all interfaces
SERVER_IP = "0.0.0.0"
TCP_PORT = 2001
UDP_PORT = 2002

server_running = True
clients = {}  # {username: socket}
inactive = set()
active = set()

def broadcast_message(message, sender=None):
    """Send a message to all connected clients except the sender."""
    for user, client_sock in list(clients.items()):
        if sender and user == sender: # Skip the sender
            continue
        try:
            client_sock.sendall(message.encode()) # Send the message
        except:
            # If sending fails, remove client
            client_sock.close()
            del clients[user]

def handle_client(client_sock, username):
    """Handle client communication. This runs when succesful connection has been established"""
    try:
        broadcast_message(f"{username} has joined the chat!", sender=username)
        
        while True:
            message = client_sock.recv(1024).decode()
            if not message:
                break
            
            if message.startswith("ACTIVE_USERS_REQUEST:"):
                user_requesting = message.split(":")[1].strip()
                user_status_list = []
                for user in clients.keys():
                    if user in active:
                        status = "active"
                    else:
                        status = "inactive"
                    user_status_list.append(f"{user} ({status})")
                response = "Active users: " + ", ".join(user_status_list)
                clients[user_requesting].sendall(response.encode())

            else:
                if username in inactive:
                    inactive.remove(username)
                    active.add(username)
                    broadcast_message(f"{username} is now active.")
                broadcast_message(message, sender=username)
    
    except:
        pass
    finally:
        #Cleanup in case
        if username in active:
            active.remove(username)
        if username in inactive:
            inactive.remove(username)
        # Remove client and notify others
        del clients[username]
        broadcast_message(f"{username} has left the chat.")
        client_sock.close()

def start_server():
    """Start the chat server with both TCP and UDP."""
    global server_running
    # TCP Server setup
    tcp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM) 
    tcp_server_sock.bind((SERVER_IP, TCP_PORT))
    tcp_server_sock.listen(5)

    # UDP Server setup
    udp_server_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_server_sock.bind((SERVER_IP, UDP_PORT))

    print(f"Server running on {SERVER_IP}:{TCP_PORT} (TCP) and {SERVER_IP}:{UDP_PORT} (UDP)")

    def accept_clients_tcp():
        """Accept and handle TCP clients while the server is running."""
        while server_running:
            try:
                client_sock, addr = tcp_server_sock.accept() # New attempt connected
            except OSError:
                break  # Stop accepting new connections when shutting down
            print(f"New TCP connection from {addr}")

            # Receive username
            username = client_sock.recv(1024).decode().strip()
            if username in clients:
                client_sock.sendall("ERROR: Username already taken.".encode()) # Send ERROR if taken
                client_sock.close()
                continue
            
            # Add to actives and clients
            clients[username] = client_sock 
            active.add(username)

            # Send online users list
            online_users = "Online users: " + ", ".join(clients.keys())
            client_sock.sendall(online_users.encode())

            # Start handling the client in a new thread
            threading.Thread(target=handle_client, args=(client_sock, username), daemon=True).start()

    def accept_clients_udp():
        """Accept and handle UDP clients (for status updates). \n
                3 types of responses expected:
                    INACTIVE: Username is now idle
                    ACTIVE: Username is now active
                    OFFLINE: Username is disconnected
        """
        while server_running:
            try:
                message, addr = udp_server_sock.recvfrom(1024)
                message = message.decode().strip()
                print(f"UDP MESSAGE: {message}")
                # If Active or inactive switch and register with right set as well as tcp messages for other clients
                if message.startswith("INACTIVE:"):
                    username = message.split(":")[1].strip()
                    if username in active:
                        active.remove(username)
                        inactive.add(username)
                        broadcast_message(f"{username} is now idle.", username)

                elif message.startswith("ACTIVE:"):
                    username = message.split(":")[1].strip()
                    if username in inactive:
                        inactive.remove(username)
                        active.add(username)
                        broadcast_message(f"{username} is now active.", username)

            except:
                pass

    # Start accepting TCP and UDP clients in separate threads
    tcp_thread = threading.Thread(target=accept_clients_tcp, daemon=True)
    udp_thread = threading.Thread(target=accept_clients_udp, daemon=True)
    tcp_thread.start()
    udp_thread.start()

    # Command loop for server shutdown
    while server_running:
        command = input("Type 'stop' to shut down the server: ").strip().lower()
        if command == "stop":
            server_running = False
            break

    print("Shutting down server...")

    # Close all client connections gracefully
    for user, client_sock in list(clients.items()):
        client_sock.sendall("Server is shutting down...".encode())
        client_sock.close()
    clients.clear()

    tcp_server_sock.close()
    udp_server_sock.close()
    print("Server stopped.")

if __name__ == "__main__":
    start_server()