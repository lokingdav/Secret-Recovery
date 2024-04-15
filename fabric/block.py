import json
from fabric.transaction import Transaction, Signer
from skrecovery import helpers, database, config

class BlockHeader:
    def __init__(self) -> None:
        self.number: int = 0
        self.chainid: str = 'skrec'
        self.data_hash: str = None
        self.previous_hash: str = None
    
    def update_from_last_block(self, block: dict):
        if block and 'header' in block:
            self.previous_hash = block['header']['data_hash']
            self.number = int(block['header']['number']) + 1
    
    def to_dict(self):
        return {
            'number': self.number,
            'chainid': self.chainid,
            'data_hash': self.data_hash,
            'previous_hash': self.previous_hash
        }
        
    @staticmethod
    def from_dict(data: dict) -> 'BlockHeader':
        header = BlockHeader()
        header.number = int(data['number'])
        header.chainid = data['chainid']
        header.data_hash = data['data_hash']
        header.previous_hash = data['previous_hash']
        return header
        
class BlockData:
    def __init__(self, transactions: list[Transaction] = []):
        self.transactions = transactions
        
    def add_tx(self, tx: dict | Transaction):
        tx: Transaction = Transaction.from_dict(tx) if isinstance(tx, dict) else tx
        self.transactions.append(tx)
        return tx.get_id()
        
    def reset(self):
        self.transactions = []
        
    def get_hash(self):
        return helpers.hash256(helpers.stringify(self.to_dict()))
    
    def to_dict(self):
        return [tx.to_dict() for tx in self.transactions]
    
    def size(self):
        return len(helpers.stringify(self.to_dict()).encode('utf-8'))
    
    @staticmethod
    def from_dict(txs: dict):
        txs = [Transaction.from_dict(tx) for tx in txs]
        return BlockData(txs)
    
class BlockMetaData:
    def __init__(self, bitmap: dict = None, creator: Signer = None):
        self.bitmap: dict = bitmap
        self.creator: Signer = creator
        self.verifiers: list[Signer] = []
        self.last_config_block_number: int = 0
        self.datasize_mb: float = 0
        
    def to_dict(self) -> dict:
        creator = self.creator.to_dict() if self.creator else None
        return {
            'bitmap': self.bitmap, 
            'creator': creator,
            'datasize_mb': self.datasize_mb,
            'verifiers': [v.to_dict() for v in self.verifiers],
            'last_config_block_number': self.last_config_block_number
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'BlockMetaData':
        creator = Signer.from_dict(data['creator']) if data['creator'] else None
        metadata: BlockMetaData = BlockMetaData(data['bitmap'], creator)
        metadata.verifiers = [Signer.from_dict(v) for v in data['verifiers']]
        metadata.last_config_block_number = data['last_config_block_number']
        metadata.datasize_mb = data.get('datasize_mb', 0)
        return metadata
        
class Block:
    def __init__(self, init=True, latest_block: dict = None) -> None:
        if init:
            self.header = BlockHeader()
            latest_block: dict = latest_block if latest_block else database.get_latest_block()
            self.header.update_from_last_block(latest_block)
            self.data = BlockData()
            self.metadata = BlockMetaData()
        else:
            self.header: BlockHeader = None
            self.data: BlockData = None
            self.metadata: BlockMetaData = None
            
    def get_number(self):
        return self.header.number
        
    def set_data_hash(self):
        self.header.data_hash = self.data.get_hash()
        
    def get_signable_data(self):
        return {
            'data': self.data.to_dict(),
            'previous_hash': self.header.previous_hash,
        }
        
    def calc_datasize(self):
        self.metadata.datasize_mb = round(self.data.size() / 1024 / 1024, 3)
        
    def save(self):
        self.calc_datasize()
        database.save_block(self.to_dict())
        
    def size(self):
        return len(helpers.stringify(self.to_dict()).encode('utf-8'))
        
    def verify(self):
        # verify creator signature
        if not self.metadata.creator.verify(self.get_signable_data()):
            print('Creator signature invalid')
            return False
        
        # verify verifiers signatures
        counter, quorom = 0, 2 * config.NUM_FAULTS + 1
        
        for verifier in self.metadata.verifiers:
            if verifier.verify(self.get_signable_data()):
                counter += 1

        return counter >= quorom
            
    def verify_previous_block(self, prev_block: 'Block'):
        return self.header.previous_hash == prev_block.header.data_hash
    
    def find_transaction_by_id(self, txid: str):
        for tx in self.data.transactions:
            if tx.get_id() == txid:
                return tx
        return None
    
    def find_transaction_by_type(self, txtype: str | list[str]):
        for tx in self.data.transactions:
            if tx.get_type() == txtype:
                return tx
        return None
    
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
        block: Block = Block(init=False)
        block.header = BlockHeader.from_dict(data['header'])
        block.data = BlockData.from_dict(data['data'])
        block.metadata = BlockMetaData.from_dict(data['metadata'])
        return block
        
    @staticmethod
    def from_number(number: int):
        data = database.find_block_by_number(number)
        return Block.from_dict(data)