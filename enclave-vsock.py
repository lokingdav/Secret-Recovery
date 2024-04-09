import socket
import vsock

if __name__ == "__main__":
    server: socket.socket = vsock.server_create()
    vsock.server_start(server)