import json
from . import store
from rq import Queue
from redis import Redis
from . import config
from . import sigma
import random

queue = Queue(connection=Redis())

def init(miners = 5):
    store.save(config.LEDGER_MINERS_COUNT, miners)
    for i in range(miners):
        key = config.LEDGER_MINERS + f":{i}"
        if store.find(key):
            continue
        priv_k, pub_k = sigma.keygen()
        priv_k, pub_k = bytes(priv_k).hex(), bytes(pub_k).hex()
        store.save(key, f"{priv_k}:{pub_k}")

def process_trnx(miner, payload):
    """Job to be run in the background"""
    print(f"Processing transaction {payload} by miner {miner}")

def post(payload):
    """Post a new transaction to the ledger"""
    miners = store.find(config.LEDGER_MINERS_COUNT, int)
    miner = random.randint(0, miners - 1)
    queue.enqueue(process_trnx, miner, payload)
    
    
class transaction:
    def __init__(self, data):
        self.data = data
        self.signature = None
        
    def __bytes__(self):
        return bytes(json.dumps(self.data), "utf-8")