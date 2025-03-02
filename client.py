import socket
import threading
import sys
import time

IDLE_TIMEOUT = 120
SERVER_IP = "127.0.0.1"
TCP_PORT = 5001
UDP_PORT = 5002

active_time = time.time()

def receive_messages(tcp_sock):
    """Listens for incoming messages from the chat server."""
    while True:
        try:
            message = tcp_sock.recv(1024).decode()
            if not message:
                break
            # Print on a new line and refresh input prompt
            sys.stdout.write("\r" + message + "\n> ")
            sys.stdout.flush()
        except:
            break
        
def check_time():
    global active_time
    while True:
        time.sleep(15)
        idle = time.time() - active_time
        if idle >= IDLE_TIMEOUT:
            send_udp_message(f"INACTIVE: {username}")
            print("You are now idle.\n>")
        else:
            send_udp_message(f"ACTIVE: {username}")
        

def send_udp_message(msg):
    """Sends a UDP status update to the server."""
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    udp_sock.sendto(msg.encode(), (SERVER_IP, UDP_PORT))

def start_client():
    """Connects to the chat server and starts sending messages."""
    global username, active_time
    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username cannot be empty.")
            continue

        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((SERVER_IP, TCP_PORT))
        
        try:
            tcp_sock.sendall(username.encode())  
            response = tcp_sock.recv(1024).decode().strip()
            if response.startswith("ERROR"):
                print(response)  # Print error message from server
                tcp_sock.close()
                continue  # Prompt for a new username
            else:
                print(response)  # Print online users list
                break  # Username accepted
        except:
            print("Connection error. Please try again.")
            tcp_sock.close()
            return
    
    send_udp_message(f"ACTIVE: {username}")
    
    threading.Thread(target=receive_messages, args=(tcp_sock,), daemon=True).start()
    
    threading.Thread(target=check_time, daemon=True).start()

    while True:
        try:
            # Using sys.stdout.write avoids issues with input() being overwritten by other threads
            sys.stdout.write("> ")
            sys.stdout.flush()
            msg = sys.stdin.readline().strip()
            
            if msg.lower() == "exit":
                break
            tcp_sock.sendall(f"{username}: {msg}".encode())
            active_time = time.time()
        except KeyboardInterrupt:
            break

    tcp_sock.close()
    send_udp_message(f"OFFLINE: {username}")
    print("\nDisconnected from server.")

if __name__ == "__main__":
    start_client()
