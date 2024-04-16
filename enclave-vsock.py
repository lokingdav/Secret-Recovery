import socket
import vsock
import psutil

def system_info():
    print("*******************************************************************")
    print("vCPU:", psutil.cpu_percent(interval=1))  # CPU utilization over the specified interval
    print("Mem", psutil.virtual_memory())         # RAM usage statistics
    print("Partitions", psutil.disk_partitions())        # Disk partition information
    print("*******************************************************************")

if __name__ == "__main__":
    system_info()
    server: socket.socket = vsock.server_create()
    vsock.server_start(server)