import argparse
from skrecovery.client import Client
from skrecovery.server import Server
from experiments.misc import get_client, get_cloud
from skrecovery.helpers import Benchmark
from experiments.store import client_secret_info

def main(num_runs, test_name):
    test_name = "retrieve"
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
        
        assert plaintext == client_secret_info
        
        print(f'\nBenchmarks for run {i+1}')
        print('client:', client_bm.entries, client_bm.total())
        print('cloud:', cloud_bm.entries, cloud_bm.total())
        
        client_bm.save().reset()
        cloud_bm.save().reset()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Retrieve script')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of runs')
    parser.add_argument('-t', '--test_name', type=str, default='retrieve', help='Name of the test')
    args = parser.parse_args()
    
    main(num_runs=args.num_runs, test_name=args.test_name)