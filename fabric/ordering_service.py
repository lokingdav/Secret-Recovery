import argparse, time, random
from fabric.setup import load_MSP, MSP
from skrecovery import helpers, database, sigma
from fabric.transaction import Transaction, TxHeader, TxType, TxSignature
from fabric.block import BlockData, BlockMetaData, BlockHeader, Block

msp: MSP = load_MSP()

class OSNode:
    index: int
    vk: sigma.PublicKey
    sk: sigma.SecretKey
    
    def __init__(self, index: int) -> None:
        self.index = index
        sk, vk = msp.orderers[index]
        self.sk, self.vk = sigma.import_priv_key(sk), sigma.import_pub_key(vk)
    
    def validate(self, tx: Transaction):
        pass
    
class OSLeader(OSNode):
    def __init__(self, index: int):
        super().__init__(index)
        
    def assemble_transactions(self, pending_txs: list[dict]):
        if not pending_txs:
            raise ValueError('No transactions to assemble')
        block: Block = Block()
        for tx_dict in pending_txs:
            block.data.add_tx(tx_dict)
        return block
            
def get_orderers():
    leader_index = random.randint(0, len(msp.orderers) - 1)
    leader, followers = None, []
    for i in range(len(msp.orderers)):
        if i == leader_index:
            leader = OSLeader(i)
        else:
            followers.append(OSNode(i))
    return leader, followers

def initialize_genesis_block_if_missing():
    # check if genesis block exists and return
    latest_block: dict = database.get_latest_block()
    if latest_block:
        return
    
    # create transaction for genesis block
    sk, vk = sigma.keygen()
    tx: Transaction = Transaction()
    tx.proposal = msp.to_dict()
    tx.response = tx.proposal
    tx.header = TxHeader(TxType.GENESIS.value)
    tx.signature = TxSignature(sigma.stringify(vk), sigma.sign(sk, tx.proposal))
    tx.endorse(msp)
    
    leader, followers = get_orderers()
    block: Block = begin_consensus(leader, followers, [tx.to_dict()])
    block.save()

def begin_consensus(pending_txs: list[dict], leader: OSLeader, followers: list[OSNode]):
    # 1. The leader assembles transactions
    block: Block = leader.assemble_transactions(pending_txs)

def start_ordering_service(args):
    leader, followers = get_orderers()
    
    while True:
        start_time = helpers.startStopwatch()
        transactions = database.get_pending_txs()
        begin_consensus(leader, followers)
        elapsed = helpers.stopStopwatch(start_time, secs=True)
        if elapsed < 2:
            time.sleep(2 - elapsed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start ordering service simulation.')
    args = parser.parse_args()
    
    initialize_genesis_block_if_missing()
    # start_ordering_service(args)