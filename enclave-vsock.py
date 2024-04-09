import socket
import skrecovery.vsock as vsock

if __name__ == "__main__":
    server: socket.socket = vsock.server_create()
    vsock.server_start(server)