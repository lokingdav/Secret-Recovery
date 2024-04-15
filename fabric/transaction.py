from enum import Enum
from crypto import sigma
import datetime, uuid, random
from skrecovery import config, database, helpers

class TxType(Enum):
    FAKE = 'fake'
    GENESIS = 'genesis'
    REQUEST = 'request'
    OPENING = 'opening'
    OPEN_RESPONSE = 'open-response'
    RESPONSE = 'response'
    COMMITMENT = 'commitment'
    PERMISSION = 'permission'
    SERVER_REGISTER = 'server-register'
    CLIENT_REGISTER = 'client-register'
    AUTHORIZE_REGISTRATION = 'authorize-registration'

class TxHeader:
    def __init__(self, txtype: str, txid: str = None) -> None:
        self.txtype = txtype
        self.txid = uuid.uuid4().hex if txid is None else txid
    
    def to_dict(self):
        return {'txid': self.txid, 'txtype': self.txtype}
    
    @staticmethod
    def from_dict(data: dict) -> 'TxHeader':
        instance = TxHeader(txtype=data['txtype'])
        instance.txid = data['txid']
        return instance
    
class Endorsement:
    def __init__(self, data: dict) -> None:
        if type(data) is not dict:
            raise ValueError('data must be a dictionary')
        self.response: dict = data
        self.signature: Signer = None
        
    def sign(self, peer_sk: str, peer_vk: str):
        sig: sigma.Signature = sigma.sign(peer_sk, self.response)
        self.signature = Signer(creator=peer_vk, signature=sig)
        
    def to_dict(self):
        return {
            'res': self.response,
            'sig': self.signature.to_dict()
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'Endorsement':
        instance = Endorsement(data['res'])
        instance.signature = Signer.from_dict(data['sig'])
        return instance

class Signer:
    def __init__(self, creator: str, signature: sigma.Signature) -> None:
        self.creator: str = creator if type(creator) is str else sigma.stringify(creator)
        self.signature: sigma.Signature = signature
        
    def verify(self, data: dict, vk: str = None):
        if vk:
            return sigma.verify(vk, data, self.signature)
        
        return sigma.verify(self.creator, data, self.signature)
        
    def to_dict(self):
        sig = sigma.stringify(self.signature)
        return {'creator': self.creator, 'sig': sig}
        
    @staticmethod
    def from_dict(data: dict) -> 'Signer':
        return Signer(
            creator=data['creator'], 
            signature=data['sig']
        )
        
class Transaction:
    def __init__(self) -> None:
        self.header: TxHeader = None
        self.data: dict = None
        self.response: dict = None
        self.signature: Signer = None
        self.created_at: datetime.datetime = None
        self.size_in_kb: float = None
        self.endorsements: list[Endorsement] = []
    
    def get_id(self):
        return self.header.txid
    
    def get_type(self):
        return self.header.txtype
    
    def endorse(self, msp):
        self.endorsements: list[Endorsement] = []
        peers = random.sample(msp.peers, config.NUM_ENDORSEMENTS)
        for keys in peers:
            endorsement = Endorsement(self.data)
            endorsement.sign(keys['sk'], keys['vk'])
            self.endorsements.append(endorsement)
    
    def finalize(self):
        self.created_at = datetime.datetime.now()
        self.size_in_kb = round(self.size_in_bytes() / 1024, 3)
        
    def send_to_ordering_service(self):
        data: dict = self.to_dict()
        database.insert_pending_txs(records=[data])
        
    def get_block(self) -> dict:
        return database.find_block_by_transaction_id(self.get_id())
    
    def size_in_bytes(self):
        return len(self.to_string().encode())
    
    def size(self):
        return self.size_in_bytes()
    
    def to_string(self):
        data = self.to_dict()
        return helpers.stringify(data)
    
    def to_dict(self):
        header = self.header.to_dict()
        signature = self.signature.to_dict()
        endorsements = [e.to_dict() for e in self.endorsements]
        return {
            '_id': self.get_id(),
            'header': header,
            'data': self.data,
            'response': self.response,
            'signature': signature,
            'endorsements': endorsements,
            'created_at': self.created_at.isoformat(),
            'size_in_kb': self.size_in_kb
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'Transaction':
        instance = Transaction()
        instance.header = TxHeader.from_dict(data['header'])
        instance.data = data['data']
        instance.response = data['response']
        instance.signature = Signer.from_dict(data['signature'])
        instance.endorsements = [Endorsement.from_dict(e) for e in data['endorsements']]
        instance.created_at = datetime.datetime.fromisoformat(data['created_at'])
        instance.size_in_kb = data['size_in_kb']
        return instance