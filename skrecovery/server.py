from crypto import sigma, commitment
from fabric import ledger, window
from enclave.app import TEE
from fabric.block import Block
from skrecovery.party import Party
from skrecovery import helpers, database, config
from enclave.response import EnclaveRes
from enclave.requests import EnclaveReqType
from fabric.transaction import TxType, Signer, Transaction

class Server(Party):
    def __init__(self, id: int = 0) -> None:
        id = f"s{id}"
        super().__init__(id)
        self.id: str = id
        self.regtx_id: str = None
        self.chainid: str = 'skrec'
        self.sk: sigma.PrivateKey = None
        self.vk: sigma.PublicKey = None
        
    def register(self):
        user: dict = self.load_state()
        if user and self.is_registered():
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
        if not user:
            database.insert_user(self.to_dict())
        else:
            database.update_user(self.to_dict())
        
    def authorize_registration(self, client_regtx_id: str):
        # Find client registration transaction
        block: Block = ledger.find_block_by_transaction_id(client_regtx_id)
        if not block:
            raise Exception("Client registration not found")
        regtx: Transaction = block.find_transaction_by_id(client_regtx_id)
        
        # Check if client is already registered and abort
        perm_hash: str = helpers.hash256(regtx.data)
        is_customer = database.get_server_customer(self.id, perm_hash)
        if is_customer:
            return None
        
        # Authorize client registration
        database.insert_server_customer(self.id, perm_hash)
        data = {
            'action': TxType.AUTHORIZE_REGISTRATION.value,
            'perm_info': regtx.data,
            'authorization': Signer(self.vk, sigma.sign(self.sk, regtx.data)).to_dict()
        }
        creator: Signer = Signer(self.vk, sigma.sign(self.sk, data))
        tx: Transaction = ledger.post(TxType.AUTHORIZE_REGISTRATION.value, data, creator)
        return tx

    
    def process_store(self, params: dict) -> EnclaveRes:
        data: dict = {
            'type': EnclaveReqType.STORE.value,
            'params': params
        }
        res: EnclaveRes = self.enclave_socket(data)
        return res
    
    def verify_ciphertext(self, params: dict) -> EnclaveRes:
        data: dict = {
            'type': EnclaveReqType.VERIFY_CIPHERTEXT.value,
            'params': params
        }
        res: EnclaveRes = self.enclave_socket(data)
        if res.is_valid_ctx:
            perm_hash: str = helpers.hash256(params['perm_info'])
            database.insert_ctx(self.id, perm_hash, params['ctx'])
        return res
    
    def process_remove(self, remove_req: dict) -> EnclaveRes:
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
        res: EnclaveRes = self.enclave_socket(data)
        if res.is_removed:
            perm_hash: str = helpers.hash256(remove_req['perm_info'])
            database.remove_server_customer(self.id, perm_hash)
            database.remove_ctx(self.id, perm_hash)
        return res
    
    def process_retrieve(self, retrieve_req: dict) -> EnclaveRes:
        sig_payload: dict = {
            'action': 'retrieve',
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
    
    def process_recover(self, recover_req: dict) -> EnclaveRes:
        tx_open: Transaction = ledger.wait_for_tx(tx_id=recover_req['tx_open_id'], name='opening')
        
        chal_window_c: list[Block] = self.get_chal_window_c(recover_req['regtx_id'], tx_open)
        chal_window_c = self.verify_registration_tx(chal_window_c)
        
        com_window_req: list[Block] = self.get_com_window_req(tx_open)
        if not self.verify_commitment_tx(tx_open=tx_open, com_window_req=com_window_req):
            raise Exception("Invalid commitment")
        
        chal_window_req: list[Block] = self.get_chal_window_req(tx_open)
        if not self.verify_permission_request(
            tx_open=tx_open,
            chal_window_req=chal_window_req,
            com_window_req=com_window_req
        ):
            raise Exception("Invalid permission request")
        
        # sign permission
        client_regtx: Transaction = ledger.find_transaction_by_id(recover_req['reg_tx_id'])
        perm = {
            'server_regtx': self.get_regtx().to_dict(),
            'client_regtx': client_regtx.to_dict(),
            'chal_window_c': [block.to_dict() for block in chal_window_c],
            'com_window_req': [block.to_dict() for block in com_window_req],
            'chal_window_req': [block.to_dict() for block in chal_window_req],
            'open': tx_open.data
        }
        
        return perm
        
        # Post to ledger
        data = {
            'action': 'permission',
            'client_regtx': recover_req['reg_tx_id'],
            'chal_window_c': {
                'start': chal_window_c[0].get_number(),
                'end': chal_window_c[-1].get_number()
            },
            'com_window_req': {
                'start': com_window_req[0].get_number(),
                'end': com_window_req[-1].get_number()
            },
            'chal_window_req': {
                'start': chal_window_req[0].get_number(),
                'end': chal_window_req[-1].get_number()
            },
        }
        creator: Signer = Signer(self.vk, sigma.sign(self.sk, data))
        ledger.post(TxType.PERMISSION.value, data, creator)
        
        enclave_req: dict = {
            'type': EnclaveReqType.RECOVER.value,
            'params': {
                'perm': perm,
                'req': tx_open.data['message']['req']
            }
        }
        return self.enclave_socket(enclave_req)
        
    def verify_registration_tx(self, chal_window_c: list[Block]) -> list[Block]:
        return chal_window_c # optional implementation
    
    def verify_commitment_tx(self, tx_open: Transaction, com_window_req: list[Block]) -> bool:
        block_com, tx_com = window.find_commitment_for_opening(
            window=com_window_req,
            tx_open=tx_open
        )
        if not block_com or not tx_com:
            return False
        return commitment.open_com(
            com=tx_com.data['com'],
            msg=tx_open.data['message'],
            sec=tx_open.data['opening']
        )
            
    def verify_permission_request(self, tx_open: Transaction, com_window_req: list[Block], chal_window_req: list[Block]) -> list[Block]:
        blocks: list[tuple[Block, Transaction]] = window.find_other_openings(
            window=chal_window_req,
            perm_info=tx_open.data['message']['perm_info'],
            exclude=tx_open.get_id()
        )
        
        if not blocks:
            return True
        
        for block, tx_open_prime in blocks:
            block_com, tx_com = window.find_commitment_for_opening(
                window=com_window_req,
                tx_open=tx_open_prime
            )
            if not block_com:
                continue
            is_valid_opening = commitment.open_com(
                com=tx_com.data['com'],
                msg=tx_open_prime.data['message'],
                sec=tx_open_prime.data['opening']
            )
            
            distance = block.get_number() - block_com.get_number()
            
            if is_valid_opening and distance <= tx_open.data['message']['perm_info']['t_open']:
                return False
        
        return True
    
    def get_chal_window_c(self, reg_tx_id: str, tx_open: Transaction) -> list[Block]:
        t_chal: int = tx_open.data['message']['perm_info']['t_chal']
        print('reg_tx_id', reg_tx_id)
        block_containing_txc: Block = ledger.find_block_by_transaction_id(reg_tx_id)
        start = block_containing_txc.get_number() + 1 # Start after the block containing tx_open
        end = start + t_chal # End at the block containing tx_open + t_chal
        return ledger.get_blocks_in_range(start_number=start, end_number=end)
    
    def get_com_window_req(tx_open: Transaction) -> list[Block]:
        t_open: int = tx_open.data['message']['perm_info']['t_open']
        block_containing_tx_open: Block = ledger.find_block_by_transaction_id(tx_open.get_id())
        start = block_containing_tx_open.get_number() - t_open # t_open blocks before the block containing tx_open
        end = block_containing_tx_open.get_number() + config.T_OPEN_BUFFER # buffer blocks after tx_open
        return ledger.get_blocks_in_range(start_number=start, end_number=end)
    
    def get_chal_window_req(tx_open: Transaction) -> list[Block]:
        t_chal: int = tx_open.data['message']['perm_info']['t_chal']
        block_containing_tx_open: Block = ledger.find_block_by_transaction_id(tx_open.get_id())
        start = block_containing_tx_open.get_number() # Start at the block containing tx_open
        end = start + t_chal # t_chal blocks after tx_open
        return ledger.get_blocks_in_range(start_number=start, end_number=end)
    
    def enclave_socket(self, req: dict) -> EnclaveRes:
        res: dict = TEE(req)
        return EnclaveRes.deserialize(res)
    
    def setData(self, data: dict):
        super().setData(data)
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
        
        
        
        
    