from crypto.sigma import PrivateKey, PublicKey
from fabric import ledger
from skrecovery import database


class Party:
    id: str = None
    regtx_id: str = None
    vk: PublicKey = None
    sk: PrivateKey = None
    
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