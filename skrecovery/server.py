import json
from ..crypto import sigma
from fabric import ledger
from skrecovery.party import Party
from fabric.transaction import TxType, Signer, Transaction
from fabric.block import Block
from skrecovery import helpers, database
from skrecovery.client import PermInfo
from skrecovery.enclave import EnclaveReqType, EnclaveResponse

class Server(Party):
    id: str = None,
    regtx_id: str = None
    chainid: str = 'skrec'
    sk: sigma.PrivateKey = None
    vk: sigma.PublicKey = None
    
    def __init__(self, id: int = 0) -> None:
        self.id = f"s{id}"
        super().__init__()
        
    def register(self):
        user: dict = self.load_state()
        if user:
            return
        # Generate keypair
        sk, vk = sigma.keygen()
        self.sk, self.vk = sk, vk
        # Post registration to ledger
        data = {'action': 'register','vk': sigma.stringify(vk)}
        creator: Signer = Signer(self.vk, sigma.sign(self.sk, data))
        tx: Transaction = ledger.post(TxType.SERVER_REGISTER.value, data, creator)
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
            'perm_info': regtx.data,
            'authorization': Signer(self.vk, sigma.sign(self.sk, regtx.data))
        }
        creator: Signer = Signer(self.vk, sigma.sign(self.sk, data))
        tx: Transaction = ledger.post(TxType.AUTHORIZE_REGISTRATION.value, data, creator)
        self.enclave_register(regtx.data['vkc'])
        return tx
    
    def enclave_register(self, perm_hash: str, vkc: str):
        data: dict = {
            'type': EnclaveReqType.REGISTER.value,
            'params': {
                'perm_hash': perm_hash,
                'vkc': vkc
            }
        }
        res: EnclaveResponse = self.enclave_socket(data)
        return res
    
    def process_store(self, point: str, perm_info: dict, vkclient: str) -> EnclaveResponse:
        data: dict = {
            'type': EnclaveReqType.STORE.value,
            'params': {
                'point': point,
                'perm_info': perm_info,
                'vkclient': sigma.stringify(vkclient)
            }
        }
        res: EnclaveResponse = self.enclave_socket(data)
        return res
    
    def verify_ciphertext(self, perm_info: dict, ctx: str) -> EnclaveResponse:
        data: dict = {
            'type': EnclaveReqType.VERIFY_CIPHERTEXT.value,
            'params': {
                'perm_info': perm_info,
                'ctx': ctx
            }
        }
        res: EnclaveResponse = self.enclave_socket(data)
        if res.is_valid_ctx:
            perm_hash: str = helpers.hash256(perm_info)
            database.insert_ctx(self.id, perm_hash, ctx)
        return res
    
    def process_remove(self, remove_req: dict) -> EnclaveResponse:
        sig_payload: dict = {
            'action': 'remove',
            'perm_info': remove_req['perm_info']
        }
        
        if not sigma.verify(
            remove_req['perm_info']['vkc'],
            sig_payload,
            signature=remove_req['signature']):
            raise Exception("Invalid signature")
        
        data: dict = {
            'type': EnclaveReqType.REMOVE.value,
            'params': remove_req
        }
        res: EnclaveResponse = self.enclave_socket(data)
        if res.is_removed:
            perm_hash: str = helpers.hash256(remove_req['perm_info'])
            database.remove_server_customer(self.id, perm_hash)
            database.remove_ctx(self.id, perm_hash)
        return res
    
    def process_retrieve(self, retrieve_req: dict) -> EnclaveResponse:
        sig_payload: dict = {
            'action': 'remove',
            'perm_info': retrieve_req['perm_info']
        }
        
        if not sigma.verify(
            retrieve_req['perm_info']['vkc'],
            sig_payload,
            signature=retrieve_req['signature']):
            raise Exception("Invalid signature")
        
        perm_hash: str = helpers.hash256(retrieve_req['perm_info'])
        data: dict = database.retrieve_ctx(server_id=self.id, perm_hash=perm_hash)
        return data['ctx']
    
    def enclave_socket(self, data: dict) -> EnclaveResponse:
        pass
    
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
        
        
        
        
    