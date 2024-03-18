from crypto.ciphers import AESCtx
from skrecovery.client import Client
from skrecovery.server import Server
from enclave.response import EnclaveRes
from skrecovery.helpers import Benchmark
from scripts.misc import get_client, get_cloud

def main(num_runs, test_name = None):
    secret_info: str = "Dark matter is a proof of God's existence."
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    client_bm: Benchmark = Benchmark('client', test_name)
    cloud_bm: Benchmark = Benchmark('cloud', test_name)
    enclave_bm: Benchmark = Benchmark('enclave', test_name)
    
    for i in range(num_runs):
        # Client part 1: Generate diffie-hellman point
        client_bm.start()
        params: dict = client.initiate_store()
        client_bm.pause()
        
        # Cloud part 1: Forward point to enclave and receive response
        cloud_bm.start()
        res: EnclaveRes = cloud.process_store(params)
        enclave_bm.add_entry(res.time_taken)
        cloud_bm.pause()
        
        # Client part 2: Verify response, create shared key and encrypt secret
        client_bm.resume()
        client.create_shared_key(res)
        ctx_params: dict = client.symmetric_enc(secret_info)
        client_bm.end()
        
        # Cloud part 2: Forward ctx to enclave and verify ctx
        cloud_bm.resume()
        res: EnclaveRes = cloud.verify_ciphertext(ctx_params)
        enclave_bm.add_entry(res.time_taken)
        cloud_bm.end()
        client.save_state()
        
        print(f'\nBenchmarks for run {i+1}')
        print('client:', client_bm.entries, cloud_bm.total())
        print('cloud:', cloud_bm.entries, cloud_bm.total())
        print('enclave:', enclave_bm.entries)
        
        client_bm.save().reset()
        cloud_bm.save().reset()
        enclave_bm.save().reset()

if __name__ == "__main__":
    main(num_runs=100, test_name="store")