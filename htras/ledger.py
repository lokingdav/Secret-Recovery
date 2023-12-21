from . import store
from . import sigma
from . import database
import json
from .helpers import hash256, stringify
from collections import namedtuple

sk_L, vk_L, setup_k = None, None, 'ledger:setup'

def setup():
    global sk_L, vk_L
    
    keys = store.find(setup_k)
    if keys:
        sk_L, vk_L = sigma.parse_keys(keys)
    else:
        sk_L, vk_L = sigma.keygen()
        store.save(setup_k, sigma.export_keys(sk_L, vk_L))
    
    create_initial_block()
    
def get_cid(dtype=None):
    if dtype is str:
        return [sigma.stringify(vk_L)]
    return [vk_L]

def create_initial_block():
    cid = get_cid(str)
    data = stringify({
        'type': 'genesis',
        'vk_Ls': cid,
    })
    genesis = create_trnx(data=data, prev="root")
    sig = sign_trnx(genesis)
    save_block(idx=0, cid=cid, trnx=genesis, sig=sig)
    
class Block(namedtuple('Block', ['idx', 'cid', 'hash', 'data', 'prev', 'sig'])):
    TYPE_SERVER_REG = 'server-reg'
    TYPE_CLIENT_REG = 'perm-info'
    TYPE_AUTHORIZE_REG = 'authorize-reg'
    TYPE_RESPONSE = 'response'
    TYPE_REQUEST = 'request'
    
    def parse_data(self):
        return json.loads(self.data)
    
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

def post(data: dict, cid: str) -> Block:
    l_trnx = database.find('ledger', f"cid={cid}")
    l_trnx = Block(*l_trnx)
    idx = l_trnx.idx + 1
    
    trnx = create_trnx(data=data, prev=l_trnx.hash)
    sig = sign_trnx(trnx)
    return save_block(idx=l_trnx.idx + 1, cid=cid, trnx=trnx, sig=sig)

def find_block(cid: str, bid: str) -> Block:
    _block = database.find('ledger', f"cid={cid} AND idx='{bid}'")
    if not _block:
        return None
    return Block(*_block)

def save_block(idx: int, cid:str, trnx: transaction, sig: sigma.G2Element):
    block = [idx, cid, trnx.hash, trnx.data, trnx.prev, sigma.stringify(sig)]
    database.insert('ledger', [block], ['idx', 'cid', 'hash', 'data', 'prev', 'sig'])
    return Block(*block)

def create_trnx(data: dict, prev: str) -> transaction:
    trnx = transaction(data=data)
    trnx.prev = prev
    trnx.set_hash()
    return trnx

def sign_trnx(trnx: transaction):
    sig = sigma.sign(sk_L, str(trnx))
    return sig

def verify_trnx(trnx: transaction, sig: sigma.G2Element):
    return sigma.verify(vk_L, str(trnx), sig)

setup()