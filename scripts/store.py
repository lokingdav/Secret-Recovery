from crypto.ciphers import AESCtx
from skrecovery.client import Client
from skrecovery.server import Server
from skrecovery.enclave import EnclaveResponse
from scripts.misc import get_client, get_cloud

def main():
    secret_info: bytes = b"secret"
    
    client: Client = get_client()
    cloud: Server = get_cloud()
    
    # Client part 1: Generate diffie-hellman point
    A: str = client.initiate_store()
    
    # Cloud part 1: Forward point to enclave and receive response
    response: EnclaveResponse = cloud.process_store(A, client.perm_info.to_dict(), client.vk)
    
    # Client part 2: Verify response, create shared key and encrypt secret
    if not response.verify(client.enclave_vk):
        raise Exception("Invalid response from enclave")
    client.create_shared_key(response.payload['B'])
    ctx: AESCtx = client.symmetric_enc(secret_info)
    
    # Cloud part 2: Forward ctx to enclave and verify ctx
    cloud.verify_ciphertext(client.perm_info.to_dict(), ctx.to_string())

if __name__ == "__main__":
    main()