from crypto.sigma import PrivateKey, PublicKey
from fabric import ledger
from skrecovery import database


class Party:
    def __init__(self, id: str) -> None:
        self.id: str = id
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
        return self.regtx_id and self.vk and self.sk
    
    def setData(self, data: dict):
        pass