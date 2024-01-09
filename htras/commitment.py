from petlib.bn import Bn
from petlib.ec import EcGroup, EcPt

G = EcGroup()

def commit(message, secret = None):
    secret = Bn().random() if secret is None else import_secret(secret)
    msg_point: EcPt = G.hash_to_point(message)
    com: EcPt = msg_point.pt_mul(secret)

    return com, secret

def open_commitment(com, message, secret):
    com, secret = import_com(com), import_secret(secret)
    msg_point: EcPt = G.hash_to_point(message)
    com_prime: EcPt = msg_point.pt_mul(secret)

    return com == com_prime

def export_com(com: EcPt):
    if not isinstance(com, EcPt):
        raise Exception("Not a commitment")
    
    return com.export()

def import_com(com):
    if isinstance(com, EcPt):
        return com
    
    return EcPt.from_binary(com)

def export_secret(secret: Bn):
    return secret.binary()

def import_secret(secret):
    if isinstance(secret, Bn):
        return secret
    
    return Bn.from_binary(secret)