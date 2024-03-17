from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from skrecovery.helpers import Benchmark
from scripts.misc import get_client, get_cloud

def main(num_runs, test_name):
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    client_bm: Benchmark = Benchmark('client', test_name)
    cloud_bm: Benchmark = Benchmark('cloud', test_name)
    enclave_bm: Benchmark = Benchmark('enclave', test_name)
    
    for i in range(num_runs):
        # Client part 1: Initiate remove request
        remove_req: dict = client.init_remove()
        
        # Cloud part 1: Process remove request
        res: EnclaveRes = cloud.process_remove(remove_req)
        
        # Client part 2: Verify response
        client.complete_remove(res)
        

if __name__ == "__main__":
    main(num_runs=100, test_name="remove")