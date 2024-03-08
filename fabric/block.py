import json
from .transaction import Transaction
from skrecovery import helpers, sigma

class BlockHeader:
    current_hash: str = None
    previous_hash: str = None
    number: int = None
    
    def __init__(self, number, current_hash, previous_hash):
        self.number, self.current_hash, self.previous_hash = number, current_hash, previous_hash
        
class BlockData:
    transactions: list[Transaction] = None
    
    def __init__(self, transactions: list[Transaction]):
        self.transactions = transactions
        
    def get_hash(self):
        return helpers.hash256(json.dumps(self.transactions))
    
class BlockMetaData:
    creator: str = None
    bitmap: dict = None
    signature: sigma.Signature = None
    
    def __init__(self, creator, bitmap):
        self.creator, self.bitmap = creator, bitmap
        
class Block:
    header: BlockHeader = None
    data: BlockData = None
    metadata: BlockMetaData = None