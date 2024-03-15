from skrecovery.client import Client
from skrecovery.server import Server
from skrecovery.enclave import EnclaveResponse
from scripts.misc import get_client, get_cloud

def main():
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Initiate remove request
    remove_req: dict = client.init_remove()
    
    # Cloud part 1: Process remove request
    encl_res: EnclaveResponse = cloud.process_remove(remove_req)
    
    # Client part 2: Verify response
    if encl_res.verify(client.enclave_vk):
        client.complete_remove()

if __name__ == "__main__":
    main()