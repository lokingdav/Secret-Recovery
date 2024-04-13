import argparse
from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from skrecovery.helpers import Benchmark
from experiments.misc import get_client, get_cloud
from experiments.store import main as store_script

def main(num_runs, test_name):
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    client_bm: Benchmark = Benchmark('client', test_name)
    cloud_bm: Benchmark = Benchmark('cloud', test_name)
    enclave_bm: Benchmark = Benchmark('enclave', test_name)
    
    for i in range(num_runs):
        # run store first
        store_script(num_runs=1)
        
        # Client part 1: Initiate remove request
        client_bm.reset().start()
        remove_req: dict = client.init_remove()
        client_bm.pause()
        
        # Cloud part 1: Process remove request
        cloud_bm.reset().start()
        res: EnclaveRes = cloud.process_remove(remove_req)
        enclave_bm.add_entry(res.time_taken)
        cloud_bm.end()
        
        # Client part 2: Verify response
        client_bm.resume()
        client.complete_remove(res)
        client_bm.end()
        
        print(f'\nBenchmarks for run {i+1}')
        print('client:', client_bm.entries, client_bm.total())
        print('cloud:', cloud_bm.entries, cloud_bm.total())
        print('enclave:', enclave_bm.entries, enclave_bm.total())
        
        client_bm.save().reset()
        cloud_bm.save().reset()
        enclave_bm.save().reset()
        

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Remove script')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of runs')
    parser.add_argument('-t', '--test_name', type=str, default='remove', help='Name of the test')
    args = parser.parse_args()
    
    main(num_runs=args.num_runs, test_name=args.test_name)