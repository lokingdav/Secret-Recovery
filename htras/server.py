import json
from . import helpers, ledger, sigma, store, database

SERVERS = 'servers'

class server:
    id: str
    cid: str
    
    def __init__(self, id) -> None:
        self.id = f"s{id}"
        
    def register(self, cid: str):
        self.cid = cid
        key = SERVERS + ":" + self.id
        self.sk, self.vk, _1, _2 = helpers.setup(key)
        pubk_str = sigma.stringify(self.vk)
        data = json.dumps({
            'type': ledger.Block.TYPE_SERVER_REG,
            'action': 'register',
            'vk_s': pubk_str,
        })
        self.regb = ledger.post(data=data, cid=cid)
        
    def register_client(self, block: ledger.Block):
        id = block.datakey()
        client = database.query('SELECT * FROM clients WHERE id=%s', [id])
        # print(client)
        if client:
            return None
        
        database.insert('clients', [[id, block.data]], ['id', 'data'])
        
        sig = sigma.sign(self.sk, block.data)
        data = block.parse_data()
        data['type'] = ledger.Block.TYPE_AUTHORIZE_REG
        data['sig'] = sigma.stringify(sig)
        data = helpers.stringify(data)
        ledger.post(data=data, cid=self.cid)
        return sig
        
        
        
    