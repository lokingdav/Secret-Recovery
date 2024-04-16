from fabric.block import Block
from fabric.transaction import TxType, Transaction

def find_commitment_for_opening(window: list[Block], tx_open: Transaction, tx_open_block_number: int) -> tuple[Block, Transaction]:
    perm_info: dict = tx_open.data['message']['perm_info']
    
    for block in window:
        if block.get_number() > tx_open_block_number:
            continue
        for tx in block.data.transactions:
            if tx.get_type() == TxType.COMMITMENT.value:
                if tx.data['perm_info'] == perm_info:
                    if tx.get_id() == tx_open.data['tx_com']:
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

def verify_window(chain: list[Block]) -> bool:
    num_blocks = len(chain)
    for i in range(0, num_blocks):
        if not chain[i].verify():
            return False
        if i == 0:
            continue
        if not chain[i].verify_previous_block(prev_block=chain[i-1]):
            return False
    return True
