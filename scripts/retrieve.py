from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from scripts.misc import get_client, get_cloud
from skrecovery.helpers import Benchmark

def main(num_runs, test_name):
    test_name = "retrieve"
    secret_info: bytes = "Dark matter is a proof of God's existence."
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    client_bm: Benchmark = Benchmark('client', test_name)
    cloud_bm: Benchmark = Benchmark('cloud', test_name)
    
    for i in range(num_runs):
        # Client part 1: Initiate retrieve request
        client_bm.reset().start()
        retrieve_req: dict = client.init_retrieve()
        client_bm.pause()
        
        # Cloud part 1: Process retrieve request
        cloud_bm.reset().start()
        ctx: str = cloud.process_retrieve(retrieve_req)
        cloud_bm.end()
        
        # Client part 2: Decrypt and verify response
        client_bm.resume()
        plaintext: dict = client.complete_retrieve(ctx)
        client_bm.end()
        
        assert plaintext == secret_info
        
        print(f'\nBenchmarks for run {i+1}')
        print('client:', client_bm.entries, client_bm.total())
        print('cloud:', cloud_bm.entries, cloud_bm.total())
        
        client_bm.save().reset()
        cloud_bm.save().reset()

if __name__ == "__main__":
    main(num_runs=100, test_name="retrieve")