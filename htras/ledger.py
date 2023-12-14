from . import store
from . import sigma
from . import database
from helpers import hash256
from collections import namedtuple

sk_L, vk_L, setup_k = None, None, 'ledger:setup'

keys = store.find(setup_k)
if keys:
    sk_L, vk_L = sigma.parse_keys(keys)
else:
    sk_L, vk_L = sigma.keygen()
    store.save(setup_k, sigma.export_keys(sk_L, vk_L))

database.create_table('ledger', [
    'idx UInt32 NOT NULL', 'cid UInt32 NOT NULL', 
    'hash STRING', 'data STRING', 'prev STRING', 'sig STRING',
    'PRIMARY KEY idx'
])

class Block(namedtuple('Block', ['idx', 'cid', 'hash', 'data', 'prev', 'sig'])):
    def datakey(self):
        return hash256(self.data)
    
class transaction():
    def __init__(self, hash=None, data=None, prev = None):
        self.hash, self.prev, self.data = hash, prev, data
    
    def set_hash(self):
        if not self.hash:
            self.hash = hash256(f'{self.data}{self.prev}'.encode())
        
    def __str__(self):
        return f"{self.hash}{self.data}{self.prev}"

def post(data: str, cid: str) -> Block:
    latest_trnx = database.find('ledger', f"cid={cid} ORDER BY idx DESC LIMIT 1")
    trnx = create_trnx(data, cid, latest_trnx)
    sig = sign_trnx(trnx)
    idx = latest_trnx.idx + 1 if latest_trnx else 1
    return save_block(idx=idx, cid=cid, trnx=trnx, sig=sig)

def find_block(cid: str, bid: str) -> Block:
    return database.find('ledger', f"cid={cid} AND hash='{bid}'")

def save_block(idx: int, cid:str, trnx: transaction, sig: sigma.G2Element):
    block = [idx, cid, trnx.hash, trnx.data, trnx.prev, sigma.stringify(sig)]
    database.insert('ledger', [block], list(block._fields))
    return Block(*block)

def create_trnx(data: str, cid: str, latest_trnx: Block) -> transaction:
    trnx = transaction(data=data)
    trnx.prev = latest_trnx.hash if latest_trnx else f'root|{cid}'
    trnx.set_hash()
    return trnx

def sign_trnx(trnx: transaction):
    sig = sigma.sign(sk_L, str(trnx))
    return sig

def verify_trnx(trnx: transaction, sig: sigma.G2Element):
    return sigma.verify(vk_L, str(trnx), sig)