from fabric.block import Block
from skrecovery import database
from fabric.setup import load_MSP, MSP
from fabric.transaction import Transaction, TxHeader, Signer

msp: MSP = load_MSP()

def post(txType: str, proposal: dict, signature: Signer):
    if type(txType) != str:
        raise ValueError('Invalid transaction type')
    if type(proposal) != dict:
        raise ValueError('Invalid proposal')
    if type(signature) != Signer:
        raise ValueError('Invalid signature')
    
    tx = Transaction()
    tx.proposal = proposal
    tx.response = proposal
    tx.header = TxHeader(txType)
    tx.signature = signature
    tx.endorse(msp)
    tx.send_to_ordering_service()
    
    return tx

def find_block_by_transaction_id(tx_id: str) -> Block:
    block: dict = database.find_block_by_transaction_id(tx_id)
    if block is None:
        return None
    return Block.from_dict(block)