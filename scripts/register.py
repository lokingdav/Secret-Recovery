from skrecovery.server import Server
from skrecovery.client import Client
from fabric.transaction import Transaction
from skrecovery import helpers

def main():
    server: Server = Server(id=0)
    server.register()
    
    helpers.wait(3) # Wait for server registration to be processed
    
    client: Client = Client(id=0)
    client.register(server.vk)
    helpers.wait(3) # Wait for client registration to be processed
    
    tx: Transaction = server.register_client(client.regtx_id)
    client.verify_server_authorization(tx)

if __name__ == "__main__":
    helpers.wait(50)