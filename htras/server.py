from . import helpers, ledger, sigma, store, database

SERVERS = 'servers'

class server:
    def __init__(self, id) -> None:
        self.id = id
        
    def register(self, cid: str):
        self.cid = cid
        self.sk, self.vk, t_o, t_c = helpers.setup(SERVERS + f":{id}")
        pubk_str = sigma.stringify(self.vk)
        self.regb = ledger.post(data=f'register:{pubk_str}', cid=cid)
        
    def register_client(self, block: ledger.Block):
        key = 'L_s:' + str(self.id) + ':' + block.datakey()
        client = store.find(key=key)
        if client:
            return True
        store.save(key=key, value=block.data)
        sig = sigma.sign(self.sk, block.data)
        data = f'{block.data}:{sigma.stringify(sig)}'
        ledger.post(data=data, cid=self.cid)
        return sig
        
        
        
    