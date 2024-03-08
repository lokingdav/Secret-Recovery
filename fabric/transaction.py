import uuid
from enum import Enum
from skrecovery import sigma

class TxType(Enum):
    REQUEST = 'request'
    RESPONSE = 'response'
    SERVER_REGISTER = 'server-register'
    CLIENT_REGISTER = 'client-register'
    AUTHORIZE_REGISTRATION = 'authorize-registration'

class TxHeader:
    txid: str = None
    txtype: str = None
    creator: str = None
    chainid: str = 'basic'
    
    def __init__(self, creator, txtype) -> None:
        self.txtype = txtype
        self.txid = uuid.uuid4().hex
    
class Endorsement:
    peer_vk: str = None # public key of the peer
    response: dict = None # response to the proposal by the peer
    signature: sigma.Signature = None # signature of the proposal by the peer
    
    def __init__(self, proposal, peer_vk) -> None:
        if type(proposal) is not dict:
            raise ValueError('Proposal must be a dictionary')
        # No world state update so response == proposal
        self.response = proposal
        self.peer_vk = peer_vk
        
    def ensorse(self, peer_sk: str):
        self.signature = sigma.sign(peer_sk, self.response)
    
class Transaction:
    header: TxHeader = None
    signature: sigma.Signature = None
    proposal: dict = None
    response: dict = None
    endorsements: list[Endorsement] = None
    
    def to_string(self):
        pass