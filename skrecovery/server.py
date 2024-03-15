import json
from ..crypto import sigma
from fabric import ledger
from fabric.transaction import TxType, Signer, Transaction
from fabric.block import Block
from . import helpers, store, database

SERVERS = 'servers'

class Server:
    id: str = None,
    regtx_id: str = None
    chainid: str = 'skrec'
    sk: sigma.PrivateKey = None
    vk: sigma.PublicKey = None
    
    def __init__(self, id: int = 0) -> None:
        self.id = f"s{id}"
        
    def register(self):
        user: dict = database.find_user_by_id(self.id)
        
        if user:
            self.setData(user)
            return
        
        # Generate keypair
        sk, vk = sigma.keygen()
        self.sk, self.vk = sk, vk
        
        # Post registration to ledger
        proposal = {'action': 'register','vk': sigma.stringify(vk)}
        creator: Signer = Signer(proposal['vk'], sigma.sign(self.sk, proposal))
        tx: Transaction = ledger.post(TxType.SERVER_REGISTER.value, proposal, creator)
        self.regtx_id = tx.get_id()
        
        # Save to database
        database.insert_user(self.to_dict())
        
    def register_client(self, client_regtx_id: str):
        # Find client registration transaction
        block: Block = ledger.find_block_by_transaction_id(client_regtx_id)
        regtx: Transaction = block.find_transaction_by_id(client_regtx_id)
        
        # Check if client is already registered and abort
        perm_hash: str = helpers.hash256(regtx)
        is_customer = database.get_server_customer(self.id, perm_hash)
        if is_customer:
            return None
        
        # Authorize client registration
        database.insert_server_customer(self.id, perm_hash)
        data = {
            'action': TxType.AUTHORIZE_REGISTRATION.value,
            'perm_info': regtx.proposal,
            'authorization': Signer(self.vk, sigma.sign(self.sk, regtx.proposal))
        }
        creator: Signer = Signer(self.vk, sigma.sign(self.sk, data))
        tx: Transaction = ledger.post(TxType.AUTHORIZE_REGISTRATION.value, data, creator)
        return tx
    
    def setData(self, data: dict):
        self.id = data['_id']
        self.vk = sigma.import_pub_key(data['vk'])
        self.sk = sigma.import_priv_key(data['sk'])
        self.regtx_id = data['regtx_id']
        self.chainid = data['chainid']
        return self
    
    def to_dict(self):
        return {
            '_id': self.id,
            'vk': sigma.stringify(self.vk),
            'sk': sigma.stringify(self.sk),
            'regtx_id': self.regtx_id,
            'chainid': self.chainid
        }
    
    @staticmethod
    def from_dict(data: dict):
        server = Server()
        server.id = data['_id']
        server.vk = sigma.import_pub_key(data['vk'])
        server.sk = sigma.import_priv_key(data['sk'])
        server.regtx_id = data['regtx_id']
        server.chainid = data['chainid']
        return server
        
        
        
        
    