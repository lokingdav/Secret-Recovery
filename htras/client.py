from . import helpers
from . import ledger
from . import sigma

CLIENTS = "clients"

class client:
    def __init__(self, id) -> None:
        self.id = CLIENTS + f":{id}"
        
    def register(self, cid, bid):
        self.vk_s = self.get_server_vk(cid, bid)
        confs = helpers.setup(self.id)
        self.sk_c, self.vk_c, self.t_open, self.t_chal = confs
        perm_info = ':'.join([self.id, sigma.stringify(self.vk_c), self.t_open, self.t_chal, self.vk_s])
        return ledger.post(data=perm_info, cid=cid)
        
    def get_server_vk(self, cid, bid):
        reg_block: ledger.Block = ledger.find_block(cid=cid, bid=bid)
        if not reg_block:
            raise Exception("Server not found")
        vk_s = reg_block.data.split(':')[1]
        return vk_s
    
    def verify_registration(self, signature: sigma.G2Element, data: str):
        return sigma.verify(self.vk_s, signature, data)