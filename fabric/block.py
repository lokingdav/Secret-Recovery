import json
from .transaction import Transaction, Signer
from skrecovery import helpers, sigma, database

class BlockHeader:
    number: int = 0
    chainid: str = 'skrec'
    data_hash: str = None
    previous_hash: str = None
    
    def update_from_last_block(self, header: 'BlockHeader'):
        if header:
            self.previous_hash = header.data_hash
            self.number = header.number + 1
    
    def to_dict(self):
        return {
            'number': self.number,
            'chainid': self.chainid,
            'data_hash': self.data_hash,
            'previous_hash': self.previous_hash
        }
    
    def from_dict(self, data: dict):
        self.number = int(data['number'])
        self.chainid = data['chainid']
        self.data_hash = data['data_hash']
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
        return helpers.hash256(json.dumps(self.to_dict()))
    
    def to_dict(self):
        return [tx.to_dict() for tx in self.transactions]
    
    @staticmethod
    def from_dict(txs: dict):
        txs = [Transaction.from_dict(tx) for tx in txs]
        return BlockData(txs)
    
class BlockMetaData:
    bitmap: dict = None
    creator: Signer = None
    verifiers: list[Signer] = []
    last_config_block_number: int = 0
    
    def __init__(self, bitmap: dict = None, creator: Signer = None):
        self.bitmap, self.creator = bitmap, creator
        
    def to_dict(self) -> dict:
        sig = self.creator.to_dict() if self.creator else None
        return {'bitmap': self.bitmap, 'sig': sig}
    
    @staticmethod
    def from_dict(data: dict) -> 'BlockMetaData':
        sig = Signer.from_dict(data['sig']) if data['sig'] else None
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
        
    def set_data_hash(self):
        self.header.data_hash = self.data.get_hash()
        
    def get_signable_data(self):
        return {
            'data': self.data.to_dict(),
            'previous_hash': self.header.previous_hash,
        }
        
    def save(self):
        database.save_block(self.to_dict())
        
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