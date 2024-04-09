import socket, traceback
from skrecovery import vsock

def start_enclave():
    try:
        server: socket.socket = vsock.server_create()
        vsock.server_start(server)
    except Exception as e:
        print(f"Failed to start enclave: {e}")
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    start_enclave()
