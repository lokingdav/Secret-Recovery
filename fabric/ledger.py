import json, random
from .setup import load_MSP, MSP
from .transaction import Transaction, Endorsement, TxHeader, TxType, TxSignature
from skrecovery import config, sigma

msp: MSP = load_MSP()

def post(txType: TxType, proposal: dict, signature: TxSignature):
    if not type(txType) == TxType:
        raise ValueError('Invalid transaction type')
    if not type(proposal) == dict:
        raise ValueError('Invalid proposal')
    if not type(signature) == TxSignature:
        raise ValueError('Invalid signature')
    
    tx = Transaction()
    tx.proposal = proposal
    tx.response = proposal
    tx.header = TxHeader(txType)
    tx.signature = signature
    tx.endorse(msp)
    # tx.send_to_ordering_service()
    
    return tx
