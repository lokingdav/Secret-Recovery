from skrecovery.client import Client
from skrecovery.server import Server

def get_client(id: int = 0) -> Client:
    client: Client = Client(id=id)
    client.load_state()
    if not client.is_registered():
        raise Exception("Client not registered")
    return client

def get_cloud(id: int = 0) -> Server:
    server: Server = Server(id=id)
    server.load_state()
    if not server.is_registered():
        raise Exception("Server not registered")
    return server