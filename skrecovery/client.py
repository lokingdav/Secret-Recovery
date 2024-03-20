from enclave.response import EnclaveRes
from crypto import sigma, ec_group, ciphers, commitment
from fabric import ledger
from skrecovery import database, helpers
from skrecovery.party import Party
from fabric.transaction import TxType, Signer, Transaction

class PermInfo:
    def __init__(self) -> None:
        self.t_open: int = None
        self.t_chal: int = None
        self.vkc: sigma.PublicKey = None
        self.vks: sigma.PublicKey = None
    
    def to_dict(self):
        return {
            't_open': self.t_open,
            't_chal': self.t_chal,
            'vkc': sigma.stringify(self.vkc),
            'vks': sigma.stringify(self.vks)
        }
        
    @staticmethod
    def from_dict(data: dict):
        perm_info = PermInfo()
        perm_info.t_open = int(data['t_open'])
        perm_info.t_chal = int(data['t_chal'])
        perm_info.vkc = sigma.import_pub_key(data['vkc'])
        perm_info.vks = sigma.import_pub_key(data['vks'])
        return perm_info

class Client(Party):
    def __init__(self, id: int = 0) -> None:
        id = f"c{id}"
        super().__init__(id)
        self.id = id
        self.regtx_id: str = None
        self.chainid: str = 'skrec'
        self.perm_info: PermInfo = None
        self.sk: sigma.PrivateKey = None
        self.vk: sigma.PublicKey = None
        self.discrete_log: ec_group.Scalar = None
        self.enclave_vk: sigma.PublicKey = None
        self.rsakeys: ciphers.RSAKeyPair = None
        self.retK: bytes = None
        
    def register(self, vks: sigma.PublicKey):
        user: dict = self.load_state()
        if user and self.is_registered():
            return
        
        # Generate keypair
        sk, vk = sigma.keygen()
        self.sk, self.vk = sk, vk
        
        # Post registration to ledger
        data = {
            't_open': 5,
            't_chal': 5,
            'vkc': sigma.stringify(self.vk),
            'vks': sigma.stringify(vks)
        }
        self.perm_info = PermInfo.from_dict(data)
        creator: Signer = Signer(self.vk, sigma.sign(self.sk, data))
        tx: Transaction = ledger.post(TxType.CLIENT_REGISTER.value, data, creator)
        self.regtx_id = tx.get_id()
        
        if not user:
            database.insert_user(self.to_dict())
        else:
            self.save_state()
    
    def verify_server_authorization(self, tx: Transaction):
        if not isinstance(tx, Transaction):
            raise ValueError("Invalid transaction")
        
        signer: Signer = Signer.from_dict(tx.data['authorization'])
        
        if not isinstance(signer, Signer):
            raise ValueError("Invalid transaction signer")
        
        return signer.verify(
            self.perm_info.to_dict(), 
            self.perm_info.vks
        )
        
    def initiate_store(self) -> str:
        self.discrete_log, point = ec_group.random_DH()
        params: dict = {
            'point': ec_group.export_point(point),
            'perm_info': self.perm_info.to_dict(),
            'vkc': sigma.stringify(self.vk),
        }
        return params
    
    def create_shared_key(self, res: EnclaveRes):
        if not res.verify(self.enclave_vk):
            raise Exception("Invalid response from enclave")
        retK: ec_group.Point = self.discrete_log * ec_group.import_point(res.payload['t_point'])
        self.retK = bytes(retK)
        
    def symmetric_enc(self, data: bytes | str) -> dict:
        plaintext = {
            'data': data.decode('utf-8') if isinstance(data, bytes) else data,
            'perm_info': self.perm_info.to_dict(),
            'req': None,
            'res': None,
            'perm': None,
        }
        ctx: ciphers.AESCtx = ciphers.aes_enc(self.retK, plaintext)
        return {
            'ctx': ctx.to_string(),
            'perm_info': self.perm_info.to_dict(),
        }
    
    def init_remove(self) -> dict:
        data = {
            'action': 'remove',
            'perm_info': self.perm_info.to_dict(),
        }
        sig: sigma.Signature = sigma.sign(self.sk, data)
        data['signature'] = sigma.stringify(sig)
        return data
    
    def complete_remove(self, res: EnclaveRes):
        if not res.verify(self.enclave_vk):
            raise Exception("Invalid response from enclave")
        
        self.retK = None
        self.enclave_vk = None
        self.save_state()
        
    def init_retrieve(self) -> dict:
        data = {
            'action': 'retrieve',
            'perm_info': self.perm_info.to_dict(),
        }
        sig: sigma.Signature = sigma.sign(self.sk, data)
        data['signature'] = sigma.stringify(sig)
        return data
    
    def complete_retrieve(self, ctx: str) -> str:
        ctx: ciphers.AESCtx = ciphers.AESCtx.from_string(ctx)
        plaintext: bytes = ciphers.aes_dec(self.retK, ctx)
        plaintext: dict = helpers.parse_json(plaintext.decode('utf-8'))
        
        assert plaintext['perm_info'] == self.perm_info.to_dict()
        assert plaintext['req'] == None
        assert plaintext['res'] == None
        assert plaintext['perm'] == None
        return plaintext['data']
        
    def init_recover(self, z_cmd: str = None) -> dict:
        self.rsakeys: ciphers.RSAKeyPair = ciphers.rsa_keygen()
        req: dict = {
            'action': 'recover',
            'pk': self.rsakeys.export_pubkey().hex(),
        }
        tx_open: Transaction = self.generate_permission(req, z_cmd)
        return {'tx_open_id': tx_open.get_id(), 'regtx_id': self.regtx_id}
    
    def generate_permission(self, req: dict, z_cmd: str = None) -> Transaction:
        msg: dict = {
            'req': req,
            'txc_id': self.regtx_id,
            'perm_info': self.perm_info.to_dict(), 
        }
        com, open_secret = commitment.commit(message=msg)
        tx_com: Transaction = self.post_commitment(com)
        
        ledger.wait_for_tx(tx_id=tx_com.get_id(), name='commitment')
        tx_open: Transaction = self.post_opening(open_secret, message=msg)
        
        if z_cmd == 'accepted' or z_cmd == 'denied':
            tx_open = ledger.wait_for_tx(tx_id=tx_open.get_id(), name='opening')
            self.respond_to_tx_open(tx_open, z_cmd)
        
        return tx_open
            
    def post_commitment(self, com: commitment.Point):
        data: dict = {
            'com': commitment.export_com(com),
            'perm_info': self.perm_info.to_dict(),
        }
        signer: Signer = Signer(creator=self.vk, signature=sigma.sign(self.sk, data))
        return ledger.post(TxType.COMMITMENT.value, data, signer)
    
    def post_opening(self, open_secret: commitment.Scalar, message: dict):
        data: dict = {
            'message': message,
            'opening': commitment.export_secret(open_secret)
        }
        signer: Signer = Signer(creator=self.vk, signature=sigma.sign(self.sk, data))
        return ledger.post(TxType.OPENING.value, data, signer)
            
    
    def respond_to_tx_open(self, tx_open: Transaction, action: str):
        data: dict = {
            'action': action,
            'tx_open_data': tx_open.data,
        }
        sig: sigma.Signature = sigma.sign(self.sk, data)
        data['granted' if action == 'accepted' else 'denied'] = sigma.stringify(sig)
        signer: Signer = Signer(creator=self.vk, signature=sigma.sign(self.sk, data))
        return ledger.post(TxType.PERMISSION.value, data, signer)
    
    def setData(self, data: dict):
        super().setData(data)
        self.id = data['_id']
        self.vk = sigma.import_pub_key(data['vk'])
        self.sk = sigma.import_priv_key(data['sk'])
        self.regtx_id = data['regtx_id']
        self.chainid = data['chainid']
        self.perm_info = PermInfo.from_dict(data['perm_info'])
        self.retK = bytes.fromhex(data['retK']) if data['retK'] else None
        self.enclave_vk = sigma.import_pub_key(data['enclave_vk']) if data['enclave_vk'] else None
        
    def to_dict(self):
        return {
            '_id': self.id,
            'vk': sigma.stringify(self.vk),
            'sk': sigma.stringify(self.sk),
            'regtx_id': self.regtx_id,
            'chainid': self.chainid,
            'perm_info': self.perm_info.to_dict() if self.perm_info else None,
            'retK': self.retK.hex() if self.retK else None,
            'enclave_vk': sigma.stringify(self.enclave_vk) if self.enclave_vk else None,
        }
        
    def save_state(self):
        database.update_user(self.to_dict())
    
    @staticmethod
    def from_dict(data: dict):
        client = Client()
        client.id = data['_id']
        client.vk = sigma.import_pub_key(data['vk'])
        client.sk = sigma.import_priv_key(data['sk'])
        client.regtx_id = data['regtx_id']
        client.chainid = data['chainid']
        client.perm_info = PermInfo.from_dict(data['perm_info'])
        client.retK = bytes.fromhex(data['retK']) if data['retK'] else None
        client.enclave_vk = sigma.import_pub_key(data['enclave_vk']) if data['enclave_vk'] else None
        return client