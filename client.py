import socket
import threading
import sys
import time

IDLE_TIMEOUT = 120
SERVER_IP = "10.30.6.14"
TCP_PORT = 2001
UDP_PORT = 2002
SLEEP_TIME = 15

active_time = time.time()

def receive_messages(tcp_sock):
    """Listens for incoming messages from the chat server."""
    while True:
        try:
            #Getting a tcp message from the server
            message = tcp_sock.recv(1024).decode()
            if not message:
                break
            # Print on a new line and refresh input prompt
            #TODO Handle this input different, it overwrites and gets weird if you are trying to type something else
            sys.stdout.write("\r" + message + "\n> ")
            sys.stdout.flush()
        except:
            break
        
def check_time():
    """Checks the time on a basis of what is defined in SLEEP_TIME and if no action for more than IDLE_TIMEOUT sets user to INACTIVE"""
    global active_time
    while True:
        time.sleep(SLEEP_TIME)
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
    
    # Username check
    while True:
        username = input("Enter your username: ").strip()
        if not username:
            print("Username cannot be empty.")
            continue
        
        # Connect to tcp
        tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        tcp_sock.connect((SERVER_IP, TCP_PORT))
        
        try:
            tcp_sock.sendall(username.encode())  # Send the username for a check
            response = tcp_sock.recv(1024).decode().strip() # Server sends back response
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
    
    threading.Thread(target=receive_messages, args=(tcp_sock,), daemon=True).start() # Thread for receiving messages
    
    threading.Thread(target=check_time, daemon=True).start() # Thread for checking idle time

    while True:
        try:
            # Using sys.stdout.write as input() is a set function
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
