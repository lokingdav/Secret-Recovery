import json
from .transaction import Transaction, TxSignature
from skrecovery import helpers, sigma, database

class BlockHeader:
    number: int = 0
    chainid: str = 'skrec'
    current_hash: str = None
    previous_hash: str = None
    
    def __init__(self, header: 'BlockHeader' = None) -> None:
        self.update_from_last(header)
    
    def update_from_last(self, header: 'BlockHeader'):
        if header:
            self.previous_hash = header.current_hash
            self.number = header.number + 1
        else:
            self.previous_hash = None
            self.number = 1
    
    def to_string(self):
        return f"{self.number}::{self.current_hash}::{self.previous_hash}"
    
    def from_string(self, string: str):
        number, current_hash, previous_hash = string.split('::')
        self.number, self.current_hash, self.previous_hash = number, current_hash, previous_hash
        
class BlockData:
    transactions: list[Transaction] = []
    
    def __init__(self, transactions: list[Transaction] = []):
        self.transactions = transactions
        
    def add_tx(self, tx: str):
        tx: Transaction = Transaction.from_string(tx)
        self.transactions.append(tx)
        return tx.get_id()
        
    def reset(self):
        self.transactions = []
        
    def get_hash(self):
        return helpers.hash256(json.dumps(self.transactions))
    
    def to_string(self):
        return json.dumps([tx.to_string() for tx in self.transactions])
    
    @staticmethod
    def from_string(string: str):
        txs = json.loads(string)
        txs = [Transaction.from_string(tx) for tx in txs]
        return BlockData(txs)
    
class BlockMetaData:
    bitmap: dict = None
    signature: TxSignature = None
    
    def __init__(self, bitmap: dict = None, signature: TxSignature = None):
        self.bitmap, self.signature = bitmap, signature
        
    def to_string(self):
        sig = self.signature.to_string() if self.signature else None
        return json.dumps([self.bitmap, sig])
    
    @staticmethod
    def from_string(string: str):
        bitmap, sig = json.loads(string)
        sig = TxSignature.from_string(sig) if sig else None
        return BlockMetaData(bitmap, sig)
        
class Block:
    header: BlockHeader = None
    data: BlockData = None
    metadata: BlockMetaData = None
    
    def __init__(self) -> None:
        db_block = database.find('ledgers', order='id DESC')
        last_block: Block = Block.from_dict(db_block) if db_block else None
        
        self.header = BlockHeader(last_block.header if last_block else None)
        self.data = BlockData()
        self.metadata = BlockMetaData()
        
    def to_dict(self):
        return {
            'id': self.header.number,
            'chainid': self.header.chainid,
            'header': self.header.to_string(),
            'data': self.data.to_string(),
            'metadata': self.metadata.to_string()
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'Block':
        block: Block = Block()
        block.header.from_string(data['header'])
        block.data = BlockData.from_string(data['data'])
        block.metadata = BlockMetaData.from_string(data['metadata'])
        return block
        
    @staticmethod
    def from_number(number: int):
        data = database.find('ledgers', where=f"id={number}")
        return Block.from_dict(data)