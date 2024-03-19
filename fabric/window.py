from fabric.block import Block
from fabric.transaction import TxType, Transaction

def find_commitment_for_opening(window: list[Block], tx_open: Transaction) -> tuple[Block, Transaction]:
    block_open: Block = tx_open.get_block()
    perm_info: dict = tx_open.data['message']['perm_info']
    
    for block in window:
        if block.get_number() > block_open.get_number():
            continue
        for tx in block.data.transactions:
            if tx.get_type() == TxType.COMMITMENT.value and tx.data['perm_info'] == perm_info:
                return block, tx
            
    return None, None
            
def find_other_openings(window: list[Block], tx_open: Transaction) -> list[tuple[Block, Transaction]]:
    perm_info: dict = tx_open.data['message']['perm_info']
    items: list[tuple[Block, Transaction]] = []
    
    for block in window:
        for tx in block.data.transactions:
            if tx.get_id() == tx_open.get_id():
                continue
            
            if tx.get_type() == TxType.OPENING.value and tx.data['message']['perm_info'] == perm_info:
                items.append((block, tx))
    return items