from crypto.sigma import PrivateKey, PublicKey
from fabric import ledger
from skrecovery import database
from fabric.transaction import Transaction


class Party:
    def __init__(self, id: str) -> None:
        self.id: str = id
        self.regtx = None
        self.regtx_id: str = None
        self.vk: PublicKey = None
        self.sk: PrivateKey = None
    
    def load_state(self):
        user: dict = database.find_user_by_id(self.id)
        if user:
            self.setData(user)
            return user
        return None
        
    def is_registered(self):
        return self.regtx and self.vk and self.sk
    
    def setData(self, data: dict):
        self.regtx_id = data.get('regtx_id')
        self.regtx = self.get_regtx()
    
    def get_regtx(self) -> Transaction:
        return ledger.find_transaction_by_id(self.regtx_id)