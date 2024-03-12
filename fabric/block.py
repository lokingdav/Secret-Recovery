import json
from .transaction import Transaction, TxSignature
from skrecovery import helpers, sigma, database

class BlockHeader:
    number: int = 0
    chainid: str = 'skrec'
    current_hash: str = None
    previous_hash: str = None
    
    def update_from_last_block(self, header: 'BlockHeader'):
        if header:
            self.previous_hash = header.current_hash
            self.number = header.number + 1
        else:
            self.previous_hash = None
            self.number = 1
    
    def to_dict(self):
        return {
            'number': self.number,
            'chainid': self.chainid,
            'current_hash': self.current_hash,
            'previous_hash': self.previous_hash
        }
    
    def from_dict(self, data: dict):
        self.number = int(data['number'])
        self.chainid = data['chainid']
        self.current_hash = data['current_hash']
        self.previous_hash = data['previous_hash']
        
    @staticmethod
    def from_dict(data: dict) -> 'BlockHeader':
        header = BlockHeader()
        header.from_dict(data)
        return header
        
class BlockData:
    transactions: list[Transaction] = []
    
    def __init__(self, transactions: list[Transaction] = []):
        self.transactions = transactions
        
    def add_tx(self, tx: dict | Transaction):
        tx: Transaction = Transaction.from_dict(tx) if isinstance(tx, dict) else tx
        self.transactions.append(tx)
        return tx.get_id()
        
    def reset(self):
        self.transactions = []
        
    def get_hash(self):
        return helpers.hash256(json.dumps(self.transactions))
    
    def to_dict(self):
        return [tx.to_dict() for tx in self.transactions]
    
    @staticmethod
    def from_dict(txs: dict):
        txs = [Transaction.from_dict(tx) for tx in txs]
        return BlockData(txs)
    
class BlockMetaData:
    bitmap: dict = None
    signature: TxSignature = None
    
    def __init__(self, bitmap: dict = None, signature: TxSignature = None):
        self.bitmap, self.signature = bitmap, signature
        
    def to_dict(self) -> dict:
        sig = self.signature.to_dict() if self.signature else None
        return {'bitmap': self.bitmap, 'sig': sig}
    
    @staticmethod
    def from_dict(data: dict) -> 'BlockMetaData':
        sig = TxSignature.from_dict(data['sig']) if data['sig'] else None
        return BlockMetaData(data['bitmap'], sig)
        
class Block:
    header: BlockHeader = None
    data: BlockData = None
    metadata: BlockMetaData = None
    
    def __init__(self) -> None:
        latest_block: dict = database.get_latest_block()
        self.header = BlockHeader()
        self.header.update_from_last_block(latest_block)
        self.data = BlockData()
        self.metadata = BlockMetaData()
        
    def save(self):
        pass
        
    def to_dict(self):
        return {
            '_id': self.header.number,
            'chainid': self.header.chainid,
            'header': self.header.to_dict(),
            'data': self.data.to_dict(),
            'metadata': self.metadata.to_dict()
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'Block':
        block: Block = Block()
        block.header.from_dict(data['header'])
        block.data = BlockData.from_dict(data['data'])
        block.metadata = BlockMetaData.from_dict(data['metadata'])
        return block
        
    @staticmethod
    def from_number(number: int):
        data = database.find_block_by_number(number)
        return Block.from_dict(data)