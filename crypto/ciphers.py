import json
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

class AESCtx:
    def __init__(self, nonce: bytes, ctx: bytes, mac: bytes):
        self.nonce = nonce
        self.ctx = ctx
        self.mac = mac
        
    def to_hex(self) -> str:
        return self.nonce.hex() + b'.' + self.ctx.hex() + b'|' + self.mac.hex()
    
    def to_string(self) -> str:
        return self.to_hex()
    
    @staticmethod
    def from_hex(data: str) -> 'AESCtx':
        return AESCtx(*map(bytes.fromhex, data.split(b'.')))
        
class RSAKeyPair:
    def __init__(self, priv_key, pub_key):
        self.priv_key = priv_key
        self.pub_key = pub_key
        
class RSACtx:
    def __init__(self, session_ctx: bytes, aes_ctx: AESCtx):
        self.session_ctx = session_ctx
        self.aes_ctx = aes_ctx

def aes_enc(key: bytes, data: bytes | str) -> AESCtx:
    if type(data) == dict:
        data = json.dumps(data)
        
    if type(data) == str:
        data = data.encode('utf-8')
        
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ctx, mac = cipher.encrypt_and_digest(data)
    return AESCtx(nonce, ctx, mac)

def aes_dec(key: bytes, ctx: AESCtx) -> bytes:
    cipher = AES.new(key, AES.MODE_EAX, nonce=ctx.nonce)
    plaintext = cipher.decrypt(ctx.ctx)
    cipher.verify(ctx.mac)
    
    return plaintext

def rsa_keygen() -> RSAKeyPair:
    privKey = RSA.generate(2048)
    return RSAKeyPair(priv_key=privKey, pub_key=privKey.publickey())

def rsa_enc(pubKey, data: bytes) -> RSACtx:
    session_key = get_random_bytes(32)
    cipher_rsa = PKCS1_OAEP.new(pubKey)
    session_ctx: bytes = cipher_rsa.encrypt(session_key)
    aes_ctx: AESCtx = aes_enc(session_key, data)
    
    return RSACtx(session_ctx=session_ctx, aes_ctx=aes_ctx)

def rsa_dec(privKey, ctx: RSACtx) -> bytes:
    cipher_rsa = PKCS1_OAEP.new(privKey)
    session_key = cipher_rsa.decrypt(ctx.session_ctx)
    return aes_dec(session_key, ctx.aes_ctx)