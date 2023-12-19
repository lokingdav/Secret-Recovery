import secrets
from blspy import BasicSchemeMPL as sigma, PrivateKey, G1Element, G2Element

def keygen():
    privkey = sigma.key_gen(secrets.token_bytes(32))
    return (privkey, privkey.get_g1())

def sign(privkey: PrivateKey, message) -> G2Element:
    message = msg_to_bytes(message)
    privkey = import_priv_key(privkey)
    return sigma.sign(privkey, message)

def verify(pubkey: G1Element, message, signature: G2Element) -> bool:
    message = msg_to_bytes(message)
    pubkey = import_pub_key(pubkey)
    signature = import_signature(signature)
    return sigma.verify(pubkey, message, signature)

def stringify(key): 
    return bytes(key).hex()

def msg_to_bytes(msg):
    if type(msg) == str:
        return msg.encode()
    return msg

def import_signature(signature: str) -> G2Element:
    if isinstance(signature, G2Element):
        return signature
    
    return G2Element.from_bytes(bytes.fromhex(signature))

def import_priv_key(privkey: str) -> PrivateKey:
    if isinstance(privkey, PrivateKey):
        return privkey
    
    return PrivateKey.from_bytes(bytes.fromhex(privkey))

def import_pub_key(pubkey: str) -> G1Element:
    if isinstance(pubkey, G1Element):
        return pubkey
    
    return G1Element.from_bytes(bytes.fromhex(pubkey))

def parse_keys(keystr: str):
    privkey, pubkey = keystr.split(':')
    return (import_priv_key(privkey), import_pub_key(pubkey))

def export_keys(privkey: PrivateKey, pubkey: G1Element):
    return f"{stringify(privkey)}:{stringify(pubkey)}"