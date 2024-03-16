from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from scripts.misc import get_client, get_cloud
from skrecovery.helpers import print_human_readable_json

def main():
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Initiate retrieve request
    remove_req: dict = client.init_retrieve()
    
    # Cloud part 1: Process retrieve request
    ctx: str = cloud.process_retrieve(remove_req)
    
    # Client part 2: Decrypt and verify response
    plaintext: dict = client.complete_retrieve(ctx)
    print('Decrypted data:', plaintext)

if __name__ == "__main__":
    main()