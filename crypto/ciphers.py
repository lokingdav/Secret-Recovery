import psutil
from skrecovery import helpers
from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes

chunk_size: int = 100 * 1024 * 1024

class AESCtx:
    def __init__(self, nonce: bytes, ctx: bytes, mac: bytes):
        self.nonce = nonce
        self.ctx = ctx
        self.mac = mac
        
    def to_hex(self) -> str:
        return self.nonce.hex() + '.' + self.ctx.hex() + '.' + self.mac.hex()
    
    def to_string(self) -> str:
        return self.to_hex()
    
    @staticmethod
    def from_string(data: str) -> 'AESCtx':
        return AESCtx(*map(bytes.fromhex, data.split('.')))
        
class RSAKeyPair:
    def __init__(self, priv_key, pub_key):
        self.priv_key = priv_key
        self.pub_key = pub_key
        
    def export_pubkey(self) -> bytes:
        return self.pub_key.export_key()
    
    @staticmethod
    def import_key(key: bytes):
        return RSA.import_key(key)

def aes_enc(key: bytes, data: bytes | str) -> AESCtx:
    if type(data) == dict:
        data = helpers.stringify(data)
        
    if type(data) == str:
        data = data.encode('utf-8')
        
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    
    ctx = bytearray()

    # Encrypt data in chunks
    index = 0
    while index < len(data):
        chunk = data[index:index+chunk_size]
        ctx.extend(cipher.encrypt(chunk))
        index += chunk_size
    
    mac = cipher.digest()
    
    return AESCtx(nonce, bytes(ctx), mac)

def aes_dec(key: bytes, ctx: AESCtx) -> bytes:
    if key is None:
        raise Exception("decryption key must be a valid key")
    if ctx is None or not isinstance(ctx, AESCtx):
        raise Exception("ctx must be a valid AESCtx")
    
    cipher = AES.new(key, AES.MODE_EAX, nonce=ctx.nonce)
    plaintext = bytearray()

    # Decrypt data in chunks
    index = 0
    data = ctx.ctx
    while index < len(data):
        chunk = data[index:index+chunk_size]
        plaintext.extend(cipher.decrypt(chunk))
        index += chunk_size

    cipher.verify(ctx.mac)
    
    return bytes(plaintext)

class RSACtx:
    def __init__(self, session_ctx: bytes, aes_ctx: AESCtx):
        self.session_ctx = session_ctx
        self.aes_ctx = aes_ctx
        
    def to_hex(self) -> str:
        return self.session_ctx.hex() + '|' + self.aes_ctx.to_string()
    
    def to_string(self) -> str:
        return self.to_hex()
    
    @staticmethod
    def from_string(data: str) -> 'AESCtx':
        ss, aesctx = data.split('|')
        return RSACtx(bytes.fromhex(ss), AESCtx.from_string(aesctx))

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