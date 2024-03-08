from enum import Enum
from .setup import MSP
import time, uuid, random, json
from skrecovery import sigma, config, database

class TxType(Enum):
    FAKE = 'fake'
    REQUEST = 'request'
    RESPONSE = 'response'
    SERVER_REGISTER = 'server-register'
    CLIENT_REGISTER = 'client-register'
    AUTHORIZE_REGISTRATION = 'authorize-registration'

class TxHeader:
    txid: str = None
    txtype: str = None
    creator: str = None
    
    def __init__(self, txtype) -> None:
        self.txtype = txtype
        self.txid = uuid.uuid4().hex
        
    def to_string(self):
        return json.dumps({
            'txid': self.txid,
            'txtype': self.txtype
        })
    
    @staticmethod
    def from_string(string) -> 'TxHeader':
        data = json.loads(string)
        instance = TxHeader(data['txtype'])
        instance.txid = data['txid']
        return instance
    
class Endorsement:
    peer_vk: str = None # public key of the peer
    response: dict = None # response to the proposal by the peer
    signature: sigma.Signature = None # signature of the proposal by the peer
    
    def __init__(self, proposal: dict, peer_vk: str) -> None:
        if type(proposal) is not dict:
            raise ValueError('Proposal must be a dictionary')
        # No world state update so response == proposal
        self.response = proposal
        self.peer_vk = peer_vk
        
    def sign(self, peer_sk: str):
        self.signature = sigma.sign(peer_sk, self.response)
        
    def to_string(self):
        return json.dumps({
            'peer_vk': self.peer_vk,
            'response': self.response,
            'signature': sigma.stringify(self.signature)
        })
        
    @staticmethod
    def from_string(string) -> 'Endorsement':
        data = json.loads(string)
        instance = Endorsement(data['response'], data['peer_vk'])
        instance.signature = sigma.import_signature(data['signature'])
        return instance

class TxSignature:
    creator: str = None
    signature: sigma.Signature = None
    
    def __init__(self, creator, signature) -> None:
        self.creator = creator
        self.signature = signature
        
    def to_string(self):
        return json.dumps({
            'creator': self.creator,
            'signature': sigma.stringify(self.signature)
        })
        
    @staticmethod
    def from_string(string) -> 'TxSignature':
        data = json.loads(string)
        instance = TxSignature(data['creator'], sigma.import_signature(data['signature']))
        return instance
        
class Transaction:
    proposal: dict = None
    response: dict = None
    header: TxHeader = None
    signature: TxSignature = None
    endorsements: list[Endorsement] = None
    
    def endorse(self, msp: MSP):
        self.endorsements: list[Endorsement] = []
        peers = random.sample(msp.peers, config.NUM_ENDORSEMENTS)
        for (peer_sk, peer_vk) in peers:
            endorsement = Endorsement(self.proposal, peer_vk)
            endorsement.sign(peer_sk)
            self.endorsements.append(endorsement)
            
    def send_to_ordering_service(self):
        cols = ['payload', 'created_at']
        records = [self.to_string(), str(int(time.time()))]
        database.insert('pending_txs', records=records, cols=cols)
    
    def to_string(self):
        return json.dumps({
            'header': self.header.to_string(),
            'proposal': self.proposal,
            'response': self.response,
            'signature': self.signature.to_string(),
            'endorsements': [e.to_string() for e in self.endorsements]
        })
        
    @staticmethod
    def from_string(string) -> 'Transaction':
        data = json.loads(string)
        instance = Transaction()
        instance.header = TxHeader.from_string(data['header'])
        instance.proposal = data['proposal']
        instance.response = data['response']
        instance.signature = TxSignature.from_string(data['signature'])
        instance.endorsements = [Endorsement.from_string(e) for e in data['endorsements']]
        return instance