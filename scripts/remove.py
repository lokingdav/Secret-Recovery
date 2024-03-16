from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from scripts.misc import get_client, get_cloud
from skrecovery.helpers import print_human_readable_json

def main():
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Initiate remove request
    remove_req: dict = client.init_remove()
    
    # Cloud part 1: Process remove request
    res: EnclaveRes = cloud.process_remove(remove_req)
    
    # Client part 2: Verify response
    client.complete_remove(res)
    
    print_human_readable_json(res.serialize())

if __name__ == "__main__":
    main()