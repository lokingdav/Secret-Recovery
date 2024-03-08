import json, random
from .setup import load_MSP, MSP
from .transaction import Transaction, Endorsement, TxHeader, TxType
from skrecovery import config, sigma

msp: MSP = load_MSP()

def post(txType: TxType, proposal: dict, signature: sigma.Signature):
    tx = Transaction()
    tx.proposal = proposal
    tx.response = proposal
    tx.header = TxHeader(txType)
    tx.endorsements = endorse_tx(proposal)

def endorse_tx(proposal: dict):
    endorsements: list[Endorsement] = []
    peers = random.sample(msp.peers, config.NUM_ENDORSEMENTS)
    for (peer_sk, peer_vk) in peers:
        endorsement = Endorsement(proposal, peer_vk)
        endorsement.ensorse(peer_sk)
        endorsements.append(endorsement)
    return endorsements

