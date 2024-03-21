from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from skrecovery.helpers import Benchmark
from scripts.misc import get_client, get_cloud
from scripts.store import main as store_script, client_secret_info

def main(num_runs, test_name):
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    client_bm: Benchmark = Benchmark('client', test_name)
    cloud_bm: Benchmark = Benchmark('cloud', test_name)
    enclave_bm: Benchmark = Benchmark('enclave', test_name)
    
    # Just to be sure the store protocol was executed
    store_script(num_runs=1) 
        
    for i in range(num_runs):
        # Client part 1: Initiate recover request
        recover_req: dict = client.init_recover(
            benchmark=client_bm
        )
        # Not needed, but just to be sure it's not closed from the client side
        client_bm.pause() 
        
        # Cloud part 1: Process recover request
        res: EnclaveRes = cloud.process_recover(
            recover_req=recover_req,
            benchmark=cloud_bm
        )
        enclave_bm.add_entry(res.time_taken)
        # Not needed, but just to be sure it's not closed from the cloud side
        cloud_bm.end()
        
        if res.error is not None:
            raise Exception(res.error)
        
        # Client part 2: Verify response
        client_bm.resume()
        recovered_secret: str = client.complete_recover(res)
        client_bm.end()
        assert recovered_secret == client_secret_info
        
        print(f'\nBenchmarks for run {i+1}')
        print('client:', client_bm.entries, client_bm.total())
        print('cloud:', cloud_bm.entries, cloud_bm.total())
        print('enclave:', enclave_bm.entries, enclave_bm.total())
        
        client_bm.save().reset()
        cloud_bm.save().reset()
        enclave_bm.save().reset()

if __name__ == "__main__":
    main(num_runs=1, test_name="recover")