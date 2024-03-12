from enum import Enum
from .setup import MSP
import datetime, uuid, random, json, sys
from skrecovery import sigma, config, database

class TxType(Enum):
    FAKE = 'fake'
    GENESIS = 'genesis'
    REQUEST = 'request'
    RESPONSE = 'response'
    SERVER_REGISTER = 'server-register'
    CLIENT_REGISTER = 'client-register'
    AUTHORIZE_REGISTRATION = 'authorize-registration'

class TxHeader:
    txid: str = None
    txtype: str = None
    
    def __init__(self, txtype: str) -> None:
        self.txtype = txtype
        self.txid = uuid.uuid4().hex
    
    def to_dict(self):
        return {'txid': self.txid, 'txtype': self.txtype}
    
    @staticmethod
    def from_dict(data: dict) -> 'TxHeader':
        instance = TxHeader(txtype=data['txtype'])
        instance.txid = data['txid']
        return instance
    
class Endorsement:
    response: dict = None
    signature: 'TxSignature' = None
    
    def __init__(self, proposal: dict) -> None:
        if type(proposal) is not dict:
            raise ValueError('Proposal must be a dictionary')
        self.response = proposal
        
    def sign(self, peer_sk: str, peer_vk: str):
        sig: sigma.Signature = sigma.sign(peer_sk, self.response)
        self.signature = TxSignature(creator=peer_vk, signature=sig)
        
    def to_dict(self):
        return {
            'res': self.response,
            'sig': self.signature.to_dict()
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'Endorsement':
        instance = Endorsement(data['res'])
        instance.signature = TxSignature.from_dict(data['sig'])
        return instance

class TxSignature:
    creator: str = None
    signature: sigma.Signature = None
    
    def __init__(self, creator: str, signature: sigma.Signature) -> None:
        self.creator = creator
        self.signature = signature
        
    def to_dict(self):
        sig = sigma.stringify(self.signature)
        return {'creator': self.creator, 'sig': sig}
        
    @staticmethod
    def from_dict(data: dict) -> 'TxSignature':
        return TxSignature(
            creator=data['creator'], 
            signature=data['sig']
        )
        
class Transaction:
    proposal: dict = None
    response: dict = None
    header: TxHeader = None
    signature: TxSignature = None
    endorsements: list[Endorsement] = None
    
    def get_id(self):
        return self.header.txid
    
    def endorse(self, msp: MSP):
        self.endorsements: list[Endorsement] = []
        peers = random.sample(msp.peers, config.NUM_ENDORSEMENTS)
        for (peer_sk, peer_vk) in peers:
            endorsement = Endorsement(self.proposal)
            endorsement.sign(peer_sk, peer_vk)
            self.endorsements.append(endorsement)
            
    def send_to_ordering_service(self):
        data = self.to_dict()
        data['created_at'] = datetime.datetime.now()
        database.insert_pending_txs(records=[data])
    
    def size_in_bytes(self):
        return len(self.to_string().encode())
    
    def size(self):
        return self.size_in_bytes()
    
    def to_string(self):
        return json.dumps(self.to_dict())
    
    def to_dict(self):
        header = self.header.to_dict()
        signature = self.signature.to_dict()
        endorsements = [e.to_dict() for e in self.endorsements]
        return {
            '_id': self.get_id(),
            'header': header,
            'proposal': self.proposal,
            'response': self.response,
            'signature': signature,
            'endorsements': endorsements
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'Transaction':
        instance = Transaction()
        instance.header = TxHeader.from_dict(data['header'])
        instance.proposal = data['proposal']
        instance.response = data['response']
        instance.signature = TxSignature.from_dict(data['signature'])
        instance.endorsements = [Endorsement.from_dict(e) for e in data['endorsements']]
        return instance