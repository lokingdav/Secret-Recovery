from skrecovery.server import Server
from skrecovery.client import Client
from fabric.transaction import Transaction
from fabric import ledger

def main():
    print("Server registration\n")
    server: Server = Server(id=0)
    server.register()
    
    ledger.wait_for_tx(server.regtx_id) # Wait for server registration to be processed
    print("Client registration\n")
    client: Client = Client(id=0)
    client.register(server.vk)
    
    ledger.wait_for_tx(client.regtx_id) # Wait for client registration to be processed
    authorization_tx: Transaction = server.authorize_registration(client.regtx_id)
    if authorization_tx: # verify if new client
        client.verify_server_authorization(authorization_tx)

if __name__ == "__main__":
    main()