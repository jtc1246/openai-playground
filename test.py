PORTS = []
# ONLY MODIFY HERE
# PORTS.append((8080, '192.168.1.234', 8080)) # (local_port, target_host, target_port)
PORTS.append((9026, 'api.openai.com', 443))


import socket
import threading
from _thread import start_new_thread
from time import sleep
import ssl


def forward(source, target):
    while True:
        data = source.recv(1024)
        print([data])
        if not data:
            break
        target.send(data)

def forward2(source, target):
    while True:
        data = source.recv(1024)
        print([data])
        if not data:
            break
        target.send(data)


def handle_client(client_socket, target_host, target_port):
    target_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    ssl_context = ssl.create_default_context()
    ssl_context.options |= ssl.OP_NO_TLSv1  # 禁用TLS 1.0
    ssl_context.options |= ssl.OP_NO_TLSv1_1  # 禁用TLS 1.1
    target_socket = ssl_context.wrap_socket(target_socket, server_hostname=target_host)
    target_socket.connect((target_host, target_port))
    # sleep(1)

    client_thread = threading.Thread(target=forward, args=(client_socket, target_socket))
    client_thread.start()

    server_thread = threading.Thread(target=forward2, args=(target_socket, client_socket))
    server_thread.start()


def start_server(local_host, local_port, target_host, target_port):
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((local_host, local_port))
    server.listen(5)
    print(f"[*] Listening on {local_host}:{local_port}")

    while True:
        client_socket, addr = server.accept()
        print(f"[*] Accepted connection from {addr[0]}:{addr[1]}")
        client_thread = threading.Thread(target=handle_client, args=(client_socket, target_host, target_port))
        client_thread.start()


def start_all(ports):
    for port in ports:
        start_new_thread(start_server, ('0.0.0.0',) + port)


if __name__ == '__main__':
    start_all(PORTS)
    while True:
        sleep(1)
