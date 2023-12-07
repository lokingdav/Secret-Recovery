import secrets
from blspy import BasicSchemeMPL as sigma, PrivateKey, G1Element, G2Element

def keygen():
    privkey = sigma.key_gen(secrets.token_bytes(32))
    return (privkey, privkey.get_g1())

def sign(privkey: PrivateKey, message) -> G2Element:
    if type(message) == str:
        message = message.encode()
    return sigma.sign(privkey, message)
