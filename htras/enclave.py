from . import enc_dec_scheme, enc_dec_scheme, sigma, ec_group, chain

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


recovery_data = {}

valid_windows = {
    'chal_window_c': False,
    'chal_window_req': False,
    'com_window': False
}

previous_hashes = {
    'chal_window_c': None,
    'chal_window_req': None,
    'com_window': None
}

def begin_recovery(data):
    global recovery_data
    recover_data = data
    
    # verify server signature
    # sigma.verify(svk, b"recover", ssig)
    # sigma.verify(svk, b"recover", lsig)
    
# def end_recovery():
#     req_prime = b"recover" + b"|" + rec_pubk.export_key()
#     assert verify_perm() and rec_req == req_prime
    
#     retK = retKs[sigma.stringify(rec_cvk)]
#     plaintext = enc_dec_scheme.aes_dec(retK, rec_aes_ctx)
#     splited_plaintext = plaintext.split(b'|')
    
#     assert splited_plaintext[0] == rec_perm_info
    
#     rsa_ctx = enc_dec_scheme.rsa_enc(pubKey=rec_pubk, data=plaintext)
#     sig = sigma.sign(msk, enc_dec_scheme.rsa_ctx_to_bytes(rsa_ctx) + b'|' + rec_perm_info)
#     return rsa_ctx, sig

def verify_window(block, window_name):
    # No need to validate, since we are not using the chain
    if valid_windows[window_name] is False and previous_hashes[window_name] is not None:
        return False
    
    if not chain.validate_block(block):
        valid_windows[window_name] = False
        previous_hashes[window_name] = block['hash']
        return
    
    if previous_hashes[window_name] is None:
        previous_hashes[window_name] = block['hash']
        valid_windows[window_name] = True
        return
    else:
        if previous_hashes[window_name] == block['prev_hash']:
            previous_hashes[window_name] = block['hash']
            valid_windows[window_name] = True
            return
        else:
            valid_windows[window_name] = False
            previous_hashes[window_name] = block['hash']
            return False
        
def verify_chal_window_c(block):
    verify_window(block, 'chal_window_c')

def verify_chal_window_req(block):
    verify_window(block, 'chal_window_req')

def verify_com_window(block):
    verify_window(block, 'com_window')

def set_client_retK(vk_client, retK):
    global retKs
    retKs[sigma.stringify(vk_client)] = retK

def set_client_secret(vk_client, data):
    ctxs[sigma.stringify(vk_client)] = data
    
def sign(msg):
    return sigma.sign(msk, msg)

def verify_perm():
    return True