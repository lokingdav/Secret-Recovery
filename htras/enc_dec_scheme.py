from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
from Crypto.PublicKey import RSA

def aes_enc(key, data):
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ctx, mac = cipher.encrypt_and_digest(data)
    return (nonce, ctx, mac)

def aes_dec(key, ctx):
    nonce, ctx, mac = ctx
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt(ctx)
    cipher.verify(mac)
    
    return plaintext

def rsa_keygen():
    privKey = RSA.generate(2048)
    return privKey.publickey(), privKey

def rsa_enc(pubKey, data):
    session_key = get_random_bytes(32)
    cipher_rsa = PKCS1_OAEP.new(pubKey)
    session_ctx = cipher_rsa.encrypt(session_key)
    aes_ctx = aes_enc(session_key, data)
    
    return (session_ctx, aes_ctx)

def rsa_dec(privKey, ctx):
    session_ctx, aes_ctx = ctx
    cipher_rsa = PKCS1_OAEP.new(privKey)
    session_key = cipher_rsa.decrypt(session_ctx)
    return aes_dec(session_key, aes_ctx)

def rsa_ctx_to_bytes(ctx):
    session_ctx, aes_ctx = ctx
    nonce, ctx, mac = aes_ctx
    
    return session_ctx + b'|' + nonce + b'|' + ctx + b'|' + mac