import json
from . import helpers, ledger, sigma, store, database

SERVERS = 'servers'

class server:
    def __init__(self, id) -> None:
        self.id = id
        
    def register(self, cid: str):
        self.cid = cid
        key = SERVERS + ":" + str(self.id)
        self.sk, self.vk, t_o, t_c = helpers.setup(key)
        pubk_str = sigma.stringify(self.vk)
        data = json.dumps({
            'type': ledger.Block.TYPE_SERVER_REG,
            'action': 'register',
            'vk_s': pubk_str,
        })
        self.regb = ledger.post(data=data, cid=cid)
        
    def register_client(self, block: ledger.Block):
        key = 'L_s:' + str(self.id) + ':' + block.datakey()
        client = store.find(key=key)
        
        if client:
            return None
        
        store.save(key=key, value=block.data)
        
        sig = sigma.sign(self.sk, block.data)
        data = block.parse_data()
        data['type'] = ledger.Block.TYPE_AUTHORIZE_REG
        data['sig'] = sigma.stringify(sig)
        data = helpers.stringify(data)
        ledger.post(data=data, cid=self.cid)
        return sig
        
        
        
    