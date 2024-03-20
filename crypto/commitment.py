from skrecovery import helpers
from oblivious.ristretto import point as Point, scalar as Scalar

def commit(message, secret = None):
    secret = Scalar() if secret is None else import_secret(secret)
    message = to_bytes(message)
    msg_point: Point = Point.hash(message)
    com: Point = secret * msg_point
    return com, secret

def open_com(com, msg, sec) -> bool:
    com, msg, sec = import_com(com), to_bytes(msg), import_secret(sec)
    msg_point: Point = Point.hash(msg)
    com_prime: Point = sec * msg_point
    return com == com_prime

def export_com(com: Point):
    if not isinstance(com, Point):
        raise Exception("Not a commitment")
    
    return com.hex()

def import_com(com):
    if isinstance(com, Point):
        return com
    
    return Point.fromhex(com)

def export_secret(secret: Scalar):
    return secret.hex()

def import_secret(secret):
    if isinstance(secret, Scalar):
        return secret
    
    return Scalar.fromhex(secret)

def to_bytes(message):
    if isinstance(message, dict):
        message = helpers.stringify(message)
    
    if isinstance(message, str):
        return message.encode()
    
    return message