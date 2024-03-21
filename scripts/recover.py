from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from scripts.misc import get_client, get_cloud
from skrecovery.helpers import print_human_readable_json
from scripts.store import main as store_script, client_secret_info

def main():
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    store_script(num_runs=1) # Just to be sure the store protocol was executed
    
    # Client part 1: Initiate recover request
    recover_req: dict = client.init_recover()
    print(recover_req)
    
    # Cloud part 1: Process recover request
    res: EnclaveRes = cloud.process_recover(recover_req)
    if res.error is not None:
        raise Exception(res.error)
    
    # Client part 2: Verify response
    recovered_secret: str = client.complete_recover(res)
    assert recovered_secret == client_secret_info

if __name__ == "__main__":
    main()