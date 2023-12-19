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
        perm_info = helpers.stringify({
            'id': self.id, 
            'type': ledger.Block.TYPE_CLIENT_REG,
            'vk_c': sigma.stringify(self.vk_c), 
            't_open': self.t_open, 
            't_chal': self.t_chal, 
            'vk_s': self.vk_s
        })
        return ledger.post(data=perm_info, cid=cid)
        
    def get_server_vk(self, cid, bid):
        reg_block: ledger.Block = ledger.find_block(cid=cid, bid=bid)
        if not reg_block:
            raise Exception("Server not found")
        reg_block = ledger.Block(*reg_block)
        reg_data = reg_block.parse_data()
        vk_s = reg_data.get('vk_s')
        return vk_s
    
    def verify_registration(self, signature: sigma.G2Element, data: str):
        return sigma.verify(self.vk_s, data, signature)