import argparse, time, random
from fabric.setup import load_MSP, MSP
from skrecovery import helpers, database, sigma, config
from fabric.transaction import Transaction, TxHeader, TxType, Signer
from fabric.block import BlockData, BlockMetaData, BlockHeader, Block

msp: MSP = load_MSP()

class OSNode:
    index: int
    vk: sigma.PublicKey
    sk: sigma.SecretKey
    
    def __init__(self, index: int) -> None:
        self.index = index
        self.sk, self.vk = msp.orderers[index]
    
    def validate(self, block: Block):
        # blocks are trivially valid by our simulation logic
        return block
    
    def sign_block(self, block: Block):
        sig = sigma.sign(self.sk, block.get_signable_data())
        block.metadata.verifiers.append(Signer(self.vk, sig))
        return block
    
class OSLeader(OSNode):
    def __init__(self, index: int):
        super().__init__(index)
        
    def assemble_transactions(self, pending_txs: list[dict]):
        if not pending_txs:
            raise ValueError('No transactions to assemble')
        block: Block = Block()
        for tx_dict in pending_txs:
            block.data.add_tx(tx_dict)
        block.set_data_hash()
    
    def sign_block(self, block: Block):
        sig = sigma.sign(self.sk, block.get_signable_data())
        block.metadata.creator = Signer(self.vk, sig)
        return block

def begin_consensus(pending_txs: list[dict], leader: OSLeader, followers: list[OSNode]):
    # 1. The leader assembles transactions
    block: Block = leader.assemble_transactions(pending_txs)
    block: Block = leader.sign_block(block)
    
    # get random 2F+1 followers
    verifiers = random.sample(followers, 2 * config.NUM_FAULTS + 1)
    for follower in verifiers:
        block = follower.validate(block)
        block = follower.sign_block(block)
        
    # save block to database
    block.save()
       
def get_orderers():
    leader_index = random.randint(0, len(msp.orderers) - 1)
    leader, followers = None, []
    for i in range(len(msp.orderers)):
        if i == leader_index:
            leader = OSLeader(i)
        else:
            followers.append(OSNode(i))
    return leader, followers

def start_ordering_service(args):
    leader, followers = get_orderers()
    while True:
        start_time = helpers.startStopwatch()
        txs = database.get_pending_txs()
        begin_consensus(pending_txs=txs, leader=leader, followers=followers)
        database.delete_pending_txs(txs)
        elapsed = helpers.stopStopwatch(start_time, secs=True)
        if elapsed < 2:
            time.sleep(2 - elapsed)

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
    tx.signature = Signer(sigma.stringify(vk), sigma.sign(sk, tx.proposal))
    tx.endorse(msp)
    
    leader, followers = get_orderers()
    block: Block = begin_consensus(leader, followers, [tx.to_dict()])
    block.save()
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start ordering service simulation.')
    args = parser.parse_args()
    
    initialize_genesis_block_if_missing()
    # start_ordering_service(args)