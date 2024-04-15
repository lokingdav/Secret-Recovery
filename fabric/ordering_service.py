from crypto import sigma
import argparse, time, random
from fabric.block import Block
from fabric.setup import load_MSP, MSP
from skrecovery import helpers, database, config
from fabric.transaction import Transaction, TxHeader, TxType, Signer

msp: MSP = load_MSP()

class OSNode:
    def __init__(self, index: int) -> None:
        self.index = index
        self.sk = msp.orderers[index]['sk']
        self.vk = msp.orderers[index]['vk']
    
    def validate(self, block: Block):
        # blocks are trivially valid by our simulation logic
        return block
    
    def sign_block(self, block: Block):
        if not isinstance(block, Block):
            raise ValueError('Block must be an instance of Block')
        sig = sigma.sign(self.sk, block.get_signable_data())
        block.metadata.verifiers.append(Signer(self.vk, sig))
        return block
    
class OSLeader(OSNode):
    def __init__(self, index: int):
        super().__init__(index)
        
    def assemble_transactions(self, pending_txs: list[dict], prev_block: Block = None):
        # print(f'Assembling {len(pending_txs)} transactions')
        if not pending_txs:
            raise ValueError('No transactions to assemble')
        
        block: Block = Block(latest_block=prev_block)
        block.data.reset()
        for tx_dict in pending_txs:
            # print(f'Adding transaction {tx_dict["_id"]} to block')
            block.data.add_tx(tx_dict)
        block.set_data_hash()
        return block
    
    def sign_block(self, block: Block):
        if not isinstance(block, Block):
            raise ValueError('Block must be an instance of Block')
        sig = sigma.sign(self.sk, block.get_signable_data())
        block.metadata.creator = Signer(self.vk, sig)
        return block

def begin_consensus(pending_txs: list[dict], leader: OSLeader, followers: list[OSNode], prev_block: Block = None, save=True):
    if not isinstance(leader, OSLeader):
        raise ValueError('Leader must be an instance of OSLeader')
    
    for follower in followers:
        if not isinstance(follower, OSNode):
            raise ValueError('All followers must be instances of OSNode')
        
    try:
        # 1. The leader assembles transactions
        block: Block = leader.assemble_transactions(pending_txs, prev_block=prev_block)
        block: Block = leader.sign_block(block)
        
        # get random 2F+1 followers
        verifiers = random.sample(followers, 2 * config.NUM_FAULTS + 1)
        for follower in verifiers:
            block = follower.validate(block)
            block = follower.sign_block(block)
            
        # save block to database
        block.calc_datasize()
        
        if save:
            block.save()
        
        return block
    except Exception as e:
        print(f'Error in begin_consensus: {e}')
        return
       
def get_orderers():
    leader_index = random.randint(0, len(msp.orderers) - 1)
    leader, followers = None, []
    for i in range(len(msp.orderers)):
        if i == leader_index:
            leader = OSLeader(i)
        else:
            followers.append(OSNode(i))
    return leader, followers

def get_pending_txs():
    pending_txs = []
    txs = database.get_pending_txs()
    total_size_in_kb = 0
    
    for tx in txs:
        size: float = float(tx.get('size_in_kb', 0))
        if not size:
            continue
        
        if total_size_in_kb + size > config.PREFERRED_MAX_BLOCK_SIZE_KB:
            if len(pending_txs) == 0:
                pending_txs.append(tx)
            break
        
        total_size_in_kb += size
        pending_txs.append(tx)
    print(f'Found {len(pending_txs)} pending transactions with size {round(total_size_in_kb / 1024, 2)} MB.')
    return pending_txs

def start_ordering_service(args):
    leader, followers = get_orderers()
    while True:
        start_time = helpers.startStopwatch()
        txs = get_pending_txs()
        # print(f'Found {len(txs)} pending transactions')
        begin_consensus(pending_txs=txs, leader=leader, followers=followers)
        database.delete_pending_txs(txs)
        # print(f'Deleted {len(txs)} pending transactions')
        elapsed = helpers.stopStopwatch(start_time, secs=True)
        if elapsed < 2:
            time.sleep(2 - elapsed)
            
        print(f'Elapsed time: {elapsed} seconds. \nSleep time: {2 - elapsed} seconds. \n')

def initialize_genesis_block_if_missing():
    # check if genesis block exists and return
    latest_block: dict = database.get_latest_block()
    if latest_block:
        return
    
    # create transaction for genesis block
    sk, vk = sigma.keygen()
    tx: Transaction = Transaction()
    tx.data = msp.to_dict()
    tx.header = TxHeader(TxType.GENESIS.value)
    tx.signature = Signer(sigma.stringify(vk), sigma.sign(sk, tx.data))
    tx.endorse(msp)
    tx.finalize()
    
    leader, followers = get_orderers()
    begin_consensus(pending_txs=[tx.to_dict()], leader=leader, followers=followers)
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start ordering service simulation.')
    args = parser.parse_args()
    helpers.print_human_readable_json(config.ORDER_SERVICE_CONFIG)
    initialize_genesis_block_if_missing()
    start_ordering_service(args)