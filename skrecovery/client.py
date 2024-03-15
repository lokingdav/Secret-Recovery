from ..crypto import sigma
from . import database
from fabric.transaction import TxType, Signer, Transaction
from fabric import ledger


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

class Client:
    id: str = None
    regtx_id: str = None
    chainid: str = 'skrec'
    perm_info: PermInfo = None
    sk: sigma.PrivateKey = None
    vk: sigma.PublicKey = None
    
    def __init__(self, id: int = 0) -> None:
        self.id = f"c{id}"
        
    def register(self, vks: sigma.PublicKey):
        user: dict = database.find_user_by_id(self.id)
        
        if user:
            self.setData(user)
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
        if not isinstance(tx.data['authorization'], Signer):
            raise ValueError("Invalid transaction signer")
        
        return tx.data['authorization'].verify(
            self.perm_info.to_dict(), 
            self.perm_info.vks
        )
        
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
            'chainid': self.chainid,
            'perm_info': self.perm_info.to_dict()
        }
    
    @staticmethod
    def from_dict(data: dict):
        client = Client()
        client.id = data['_id']
        client.vk = sigma.import_pub_key(data['vk'])
        client.sk = sigma.import_priv_key(data['sk'])
        client.regtx_id = data['regtx_id']
        client.chainid = data['chainid']
        client.perm_info = PermInfo.from_dict(data['perm_info'])
        return client