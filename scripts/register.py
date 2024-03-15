from skrecovery.server import Server
from skrecovery.client import Client
from fabric.transaction import Transaction
from skrecovery import helpers
import traceback

def main():
    print("Server registration\n")
    server: Server = Server(id=0)
    server.register()
    
    helpers.wait(3) # Wait for server registration to be processed
    print("Client registration\n")
    client: Client = Client(id=0)
    client.register(server.vk)
    
    retries = 0
    while True:
        helpers.wait(3) # Wait for client registration to be processed
        print("Server accepts client registration\n")
        try:
            tx: Transaction = server.register_client(client.regtx_id)
            print("Client verifies server authorization")
            if tx is not None:
                client.verify_server_authorization(tx)
            break
        except Exception as e:
            traceback.print_exc()
            retries += 1
            if retries > 5:
                raise Exception("Failed to authorize client registration")

if __name__ == "__main__":
    main()