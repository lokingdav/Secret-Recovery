import socket
from enclave.app import TEE
from skrecovery import helpers

class VsockClient:
    """Client"""
    def __init__(self, conn_tmo=5):
        self.conn_tmo = conn_tmo

    def connect(self, endpoint: tuple):
        """Connect to the remote endpoint"""
        self.sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        self.sock.settimeout(self.conn_tmo)
        self.sock.connect(endpoint)

    def send_data(self, data: bytes):
        """Send data to a remote endpoint"""
        if not isinstance(data, bytes):
            raise TypeError('data must be bytes')
        
        self.sock.sendall(data)

    def recv_data(self):
        """Receive data from a remote endpoint and return it as bytes."""
        data_received = bytearray()
        while True:
            data = self.sock.recv(1024)
            if not data:
                break
            data_received.extend(data)
        return bytes(data_received)

    def disconnect(self):
        """Close the client socket"""
        self.sock.close()

class VsockServer:
    """Server"""
    def __init__(self, conn_backlog=128):
        self.conn_backlog = conn_backlog

    def bind(self, port):
        """Bind and listen for connections on the specified port"""
        self.sock = socket.socket(socket.AF_VSOCK, socket.SOCK_STREAM)
        self.sock.bind((socket.VMADDR_CID_ANY, port))
        self.sock.listen(self.conn_backlog)
        
    def receive_data(self, client: socket.socket):
        """Receive data from a remote endpoint and return it as bytes."""
        data_received = bytearray()
        while True:
            try:
                chunk = client.recv(1024)
            except socket.error:
                break
            if not chunk:
                break
            data_received.extend(chunk)
        return bytes(data_received)
        
    def process_and_respond(self, client: socket.socket):
        """Process received data and send a response"""
        data: bytes = self.receive_data(client)
        res: bytes = self.process_data(data)
        client.sendall(res)

    def process_data(self, data: bytes) -> bytes:
        """Process the received data and return a response"""
        res: dict = TEE(data)
        return helpers.stringify(res).encode('utf-8')

    def listen(self):
        """Receive data from a remote endpoint and send a response"""
        while True:
            client, (remote_cid, remote_port) = self.sock.accept()
            try:
                self.process_and_respond(client)
            finally:
                client.close()

    def send_data(self, data):
        """Send data to a remote endpoint"""
        while True:
            (to_client, (remote_cid, remote_port)) = self.sock.accept()
            to_client.sendall(data)
            to_client.close()