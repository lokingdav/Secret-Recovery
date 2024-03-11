from enum import Enum
from .setup import MSP
import datetime, uuid, random, json, sys
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
    
    def __init__(self, txtype: TxType) -> None:
        self.txtype = txtype
        self.txid = uuid.uuid4().hex
        
    def to_string(self):
        # return txid||txtype
        return f"{self.txid}::{self.txtype}"
    
    @staticmethod
    def from_string(string: str) -> 'TxHeader':
        txid, txtype = string.split('::')
        instance = TxHeader(txtype=txtype)
        instance.txid = txid
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
        res = json.dumps(self.response)
        sig = sigma.stringify(self.signature)
        return f"{self.peer_vk}::{res}::{sig}"
        
    @staticmethod
    def from_string(string: str) -> 'Endorsement':
        vk, res, sig = string.split('::')
        res = json.loads(res)
        instance = Endorsement(res, vk)
        instance.signature = sigma.import_signature(sig)
        return instance

class TxSignature:
    creator: str = None
    signature: sigma.Signature = None
    
    def __init__(self, creator: str, signature: sigma.Signature) -> None:
        self.creator = creator
        self.signature = signature
        
    def to_string(self):
        sig = sigma.stringify(self.signature)
        return f"{self.creator}::{sig}"
        
    @staticmethod
    def from_string(string: str) -> 'TxSignature':
        creator, sig = string.split('::')
        sig = sigma.import_signature(sig)
        instance = TxSignature(creator=creator, signature=sig)
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
        records = [self.to_string(), datetime.datetime.now()]
        database.insert('pending_txs', records=[records], cols=cols)
    
    def size_in_bytes(self):
        return len(self.to_string().encode())
    
    def size(self):
        return self.size_in_bytes()
    
    def to_string(self):
        # header||proposal||response||signature||endorsements
        header = self.header.to_string()
        proposal = json.dumps(self.proposal)
        response = json.dumps(self.response)
        signature = self.signature.to_string()
        endorsements = [e.to_string() for e in self.endorsements]
        endorsements = ':::'.join(endorsements)
        
        return f"{header}||{proposal}||{response}||{signature}||{endorsements}"
        
    @staticmethod
    def from_string(string: str) -> 'Transaction':
        header, proposal, response, signature, endorsements = string.split('||')
        instance = Transaction()
        instance.header = TxHeader.from_string(header)
        instance.proposal = json.loads(proposal)
        instance.response = json.loads(response)
        instance.signature = TxSignature.from_string(signature)
        instance.endorsements = [Endorsement.from_string(e) for e in endorsements.split(':::')]
        return instance