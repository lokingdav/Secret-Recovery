import json
from crypto import sigma, ec_group, ciphers
from fabric import ledger
from skrecovery import database
from skrecovery.party import Party
from fabric.transaction import TxType, Signer, Transaction


class PermInfo:
    t_open: int = None
    t_chal: int = None
    vkc: sigma.PublicKey = None
    vks: sigma.PublicKey = None
    
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
    id: str = None
    regtx_id: str = None
    chainid: str = 'skrec'
    perm_info: PermInfo = None
    sk: sigma.PrivateKey = None
    vk: sigma.PublicKey = None
    discrete_log: ec_group.Scalar = None
    enclave_vk: sigma.PublicKey = None
    retK: bytes = None
    
    def __init__(self, id: int = 0) -> None:
        self.id = f"c{id}"
        super().__init__()
        
    def register(self, vks: sigma.PublicKey):
        user: dict = self.load_state()
        if user:
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
        
        # Save to database
        database.insert_user(self.to_dict())
    
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
        return ec_group.export_point(point)
    
    def create_shared_key(self, B: str):
        retK = self.discrete_log * ec_group.import_point(B)
        self.retK = bytes(retK)
        
    def symmetric_enc(self, data: bytes) -> ciphers.AESCtx:
        plaintext = {
            'data': data,
            'perm_info': self.perm_info.to_dict(),
            'req': None,
            'res': None,
            'perm': None,
        }
        return ciphers.aes_enc(self.retK, plaintext)
    
    def init_remove(self) -> dict:
        data = {
            'action': 'remove',
            'perm_info': self.perm_info.to_dict(),
        }
        sig: sigma.Signature = sigma.sign(self.sk, data)
        data['signature'] = sigma.stringify(sig)
        return data
    
    def complete_remove(self):
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
    
    def complete_retrieve(self, ctx: str):
        ctx: ciphers.AESCtx = ciphers.AESCtx.from_string(ctx)
        plaintext = ciphers.aes_dec(self.retK, ctx)
        assert plaintext['perm_info'] == self.perm_info.to_dict()
        assert plaintext['req'] == None
        assert plaintext['res'] == None
        assert plaintext['perm'] == None
        return plaintext['data']
        
    def setData(self, data: dict):
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