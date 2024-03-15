from crypto.ciphers import AESCtx
from skrecovery.client import Client
from skrecovery.server import Server
from skrecovery.enclave import EnclaveRes
from scripts.misc import get_client, get_cloud
from skrecovery.helpers import print_human_readable_json

def main():
    secret_info: bytes = "Dark matter is a proof of God's existence."
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Generate diffie-hellman point
    params: dict = client.initiate_store()
    
    # Cloud part 1: Forward point to enclave and receive response
    res: EnclaveRes = cloud.process_store(params)
    
    # Client part 2: Verify response, create shared key and encrypt secret
    client.create_shared_key(res)
    ctx_params: dict = client.symmetric_enc(secret_info)
    
    # Cloud part 2: Forward ctx to enclave and verify ctx
    res: EnclaveRes = cloud.verify_ciphertext(ctx_params)
    print('res:', res.serialize())
    
    client.save_state()

if __name__ == "__main__":
    main()