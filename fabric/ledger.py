from fabric.block import Block
from skrecovery import database, helpers
from fabric.setup import load_MSP, MSP
from fabric.transaction import Transaction, TxHeader, Signer, TxType

msp: MSP = None

def post(txType: str, data: dict, signature: Signer, send_tos: bool = True) -> Transaction:
    if type(txType) != str:
        raise ValueError('Invalid transaction type')
    if type(data) != dict:
        raise ValueError('Invalid transaction data')
    if type(signature) != Signer:
        raise ValueError('Invalid signature')
    
    if not msp:
        setup()
    
    tx = Transaction()
    tx.data = data
    tx.header = TxHeader(txType)
    tx.signature = signature
    tx.endorse(msp)
    tx.finalize()
    
    if (send_tos):
        tx.send_to_ordering_service()
    
    return tx

def find_block_by_transaction_id(tx_id: str) -> Block:
    block: dict = database.find_block_by_transaction_id(tx_id)
    if block is None:
        return None
    return Block.from_dict(block)

def find_transaction_by_id(tx_id: str) -> Transaction:
    block: Block = find_block_by_transaction_id(tx_id)
    if block is None:
        return None
    return block.find_transaction_by_id(tx_id)

def wait_for_tx(tx_id: str, name: str = '', seconds:int = 3) -> float: 
    wait_time: helpers.Benchmark = helpers.Benchmark('wait-time')
    wait_time.reset().start()
    
    print(f"Listening to see tx {name}({tx_id}) on the ledger...")
    tx: Transaction = find_transaction_by_id(tx_id)
    while tx is None:
        helpers.wait(seconds)
        tx = find_transaction_by_id(tx_id)
    print(f"Transaction {name}({tx_id}) found on the ledger\n")
    
    return wait_time.end().total()

def get_blocks_in_range(start_number: int, end_number: int) -> list[Block]:
    items: list[dict] = database.find_blocks_in_range(start_number, end_number)
    return [Block.from_dict(item) for item in items]

def get_registration_authorization_tx(regtx: Transaction):
    filters: dict = {
        'data.header.txtype': TxType.AUTHORIZE_REGISTRATION.value,
        'data.data.perm_info': regtx.data
    }
    
    block: dict = database.find_block_by_filters(filters)
    block: Block = Block.from_dict(block)
    
    if not block:
        return None
    
    for tx in block.data.transactions:
        if tx.get_type() == TxType.AUTHORIZE_REGISTRATION.value and tx.data['perm_info'] == regtx.data:
            return tx
        
    return None

def setup():
    global msp
    msp = load_MSP()