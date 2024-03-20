from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from scripts.misc import get_client, get_cloud
from skrecovery.helpers import print_human_readable_json

def main():
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Initiate recover request
    recover_req: dict = client.init_recover()
    print(recover_req)
    # Cloud part 1: Process recover request
    res: EnclaveRes = cloud.process_recover(recover_req)
    print_human_readable_json(res)
    
    # Client part 2: Verify response
    # client.complete_recover(res)
    
    print_human_readable_json(res.serialize())

if __name__ == "__main__":
    main()