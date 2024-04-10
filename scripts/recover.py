import argparse
from skrecovery.client import Client
from skrecovery.server import Server
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
        client_bm.reset().start()
        recover_req, client_wait_time = client.init_recover()
        client_bm.pause().add_entry(-1 * client_wait_time)
        
        # Cloud part 1: Process recover request
        cloud_bm.reset().start()
        res, cloud_wait_time = cloud.process_recover(recover_req=recover_req)
        cloud_bm.end().add_entry(-1 * cloud_wait_time)
        enclave_bm.add_entry(res.time_taken)
        
        if res.error is not None:
            raise Exception(res.error)
        
        # Client part 2: Verify response
        client_bm.resume()
        recovered_secret: str = client.complete_recover(res)
        client_bm.end()
        
        assert recovered_secret == client_secret_info
        print('Recovered secret:', recovered_secret)
        
        print(f'\nBenchmarks for run {i+1}')
        print('client:', client_bm.entries, client_bm.total())
        print('cloud:', cloud_bm.entries, cloud_bm.total())
        print('enclave:', enclave_bm.entries, enclave_bm.total())
        print('\n')
        
        client_bm.save().reset()
        cloud_bm.save().reset()
        enclave_bm.save().reset()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Recover script')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of runs')
    parser.add_argument('-t', '--test_name', type=str, default='recover', help='Name of the test')
    args = parser.parse_args()
    
    main(num_runs=args.num_runs, test_name=args.test_name)