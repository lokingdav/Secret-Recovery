import socket
import vsock
import psutil

def system_info():
    print("*******************************************************************")
    print("vCPU:", psutil.cpu_percent(interval=1))
    print(f"Available Memory {round(100 - psutil.virtual_memory().percent, 2)}%")
    print("*******************************************************************")

if __name__ == "__main__":
    system_info()
    server: socket.socket = vsock.server_create()
    vsock.server_start(server)