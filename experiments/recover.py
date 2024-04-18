import argparse, pickle
from skrecovery.client import Client
from skrecovery.server import Server
from skrecovery.helpers import Benchmark
from enclave.response import EnclaveRes
from experiments.misc import get_client, get_cloud
from experiments.store import main as store_script, client_secret_info
import experiments.sim_blockchain as sim_blockchain
import skrecovery.database as database
import os, traceback

def init_recover(client: Client, cache: bool = False) -> dict:
    if not cache:
        return client.init_recover()
    
    filename = 'tmp/recover_req.pkl'
    if not os.path.exists(filename):
        recover_req = client.init_recover()
        with open(filename, 'wb') as f:
            pickle.dump(recover_req, f)
    else:
        try:
            with open(filename, 'rb') as f:
                recover_req = pickle.load(f)
        except EOFError:
            recover_req = client.init_recover()
            with open(filename, 'wb') as f:
                pickle.dump(recover_req, f)
    return recover_req

def main(num_runs, test_name):
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    sim_blockchain.init()
    
    client_bm: Benchmark = Benchmark('client', test_name)
    cloud_bm: Benchmark = Benchmark('cloud', test_name)
    enclave_bm: Benchmark = Benchmark('enclave', test_name)
    
    # Just to be sure the store protocol was executed
    store_script(num_runs=1) 
        
    for i in range(num_runs):
        try:
            # Client part 1: Initiate recover request
            client_bm.reset().start()
            recover_req = init_recover(client, cache=False)
            client_bm.pause()
            
            sim_blockchain.simulate(
                tx_com=recover_req['tx_com'],
                tx_open=recover_req['tx_open'],
                t_open=client.perm_info.t_open,
                t_chal=client.perm_info.t_chal,
                t_wait=client.perm_info.t_wait,
                cache=False
            )
            
            # Cloud part 1: Process recover request
            cloud_bm.reset().start()
            res: EnclaveRes = cloud.process_recover(recover_req=recover_req)
            cloud_bm.end()
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
            sim_blockchain.clean()
        except Exception as ex:
            sim_blockchain.clean()
            traceback.print_exc()
            raise ex

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Recover script')
    parser.add_argument('-n', '--num_runs', type=int, default=1, help='Number of runs')
    parser.add_argument('-t', '--test_name', type=str, default='recover', help='Name of the test')
    args = parser.parse_args()
    
    main(num_runs=args.num_runs, test_name=args.test_name)