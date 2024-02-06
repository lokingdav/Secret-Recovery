from . import aes, sigma, ec_group, aes

msk, mvk = None, None
retKs = {}

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
    

def verify_ciphertext(vk_client, perm_info, data):
    nonce, ctx, mac = data
    vk_client = sigma.stringify(vk_client)
    msg = aes.dec(retKs[vk_client], nonce=nonce, ctx=ctx, mac=mac)
    perm_info_prime, secret = msg.split(b'|')
    return perm_info_prime == perm_info

def remove():
    pass

def recover():
    pass

def sign(msg):
    return sigma.sign(msk, msg)