from crypto import ciphers, ec_group, sigma
from enum import Enum

class EnclaveReqType(Enum):
    STORE = 'store'
    REMOVE = 'remove'
    RECOVER = 'recover'
    RETRIEVE = 'retrieve'
    VERIFY_CIPHERTEXT = 'verify_ciphertext'
    
        