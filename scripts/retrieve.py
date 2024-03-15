from skrecovery.client import Client
from skrecovery.server import Server
from skrecovery.enclave import EnclaveRes
from scripts.misc import get_client, get_cloud

def main():
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Initiate retrieve request
    remove_req: dict = client.init_retrieve()
    
    # Cloud part 1: Process retrieve request
    ctx: str = cloud.process_remove(remove_req)
    
    # Client part 2: Decrypt and verify response
    client.complete_retrieve(ctx)

if __name__ == "__main__":
    main()