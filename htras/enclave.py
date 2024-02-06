from . import enc_dec_scheme, enc_dec_scheme, sigma, ec_group, pi_perm

msk, mvk = None, None
retKs = {}
ctxs = {}

def install():
    global msk, mvk
    if msk is None or mvk is None:
        msk, mvk = sigma.keygen()
    
def getpk():
    return mvk
    
def store(A, vk_client: str):
    global retKs
    vk_client = sigma.stringify(vk_client)
    b, B = ec_group.random_DH()
    retKs[vk_client] = b * A
    
    sig = sigma.sign(msk, f"{vk_client}|{A.hex()}|{B.hex()}")
    
    return B, vk_client, sig
    

def verify_ciphertext(vk_client, perm_info, aes_ctx):
    vk_client = sigma.stringify(vk_client)
    msg = enc_dec_scheme.aes_dec(retKs[vk_client], aes_ctx)
    perm_info_prime, secret = msg.split(b'|')
    return perm_info_prime == perm_info

def remove(vk_client, perm_info, sig):
    remove_msg = b"remove" + b"|" + perm_info
    
    if not sigma.verify(vk_client, remove_msg, sig):
        raise Exception("Invalid signature")
    
    retKs[sigma.stringify(vk_client)] = None
    
    sig = sigma.sign(msk, b"removed" + b'|' + perm_info + b"|" + bytes(sig))
    
    return sig

def recover(pubk, aes_ctx, req, perm_info, cvk):
    req_prime = b"recover" + b"|" + pubk.export_key()
    assert pi_perm.verify_perm() and req == req_prime
    
    retK = retKs[sigma.stringify(cvk)]
    plaintext = enc_dec_scheme.aes_dec(retK, aes_ctx)
    splited_plaintext = plaintext.split(b'|')
    
    assert splited_plaintext[0] == perm_info
    
    rsa_ctx = enc_dec_scheme.rsa_enc(pubKey=pubk, data=plaintext)
    sig = sigma.sign(msk, enc_dec_scheme.rsa_ctx_to_bytes(rsa_ctx) + b'|' + perm_info)
    return rsa_ctx, sig

def set_client_retK(vk_client, retK):
    global retKs
    retKs[sigma.stringify(vk_client)] = retK

def set_client_secret(vk_client, data):
    ctxs[sigma.stringify(vk_client)] = data
    
def sign(msg):
    return sigma.sign(msk, msg)