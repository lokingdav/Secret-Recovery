import argparse, time, random
from fabric.setup import load_MSP, MSP
from skrecovery import helpers, database, sigma
from fabric.transaction import Transaction
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
        
    def assemble_transactions(self):
        limit = 10000 # max number of pending transactions to fetch
        txorder = 'created_at DESC, id DESC'
        pending_txs = database.find_all('pending_txs', order=txorder, limit=limit)
        
        if len(pending_txs) < 10:
            return None
        
        batch_items = []
        # create block and update header and data
        block: Block = Block()
        block.header = BlockHeader()
        block.header.init()
        block.data = BlockData()
        
        for tx_dict in pending_txs:
            txid = block_data.add_tx(tx_dict['payload'])
            batch_items.append((txid, tx_dict['id']))
            
        return block_data, batch_items
            
def get_orderers():
    leader_index = random.randint(0, len(msp.orderers) - 1)
    leader, followers = None, []
    
    for i in range(len(msp.orderers)):
        if i == leader_index:
            leader = OSLeader(i)
        else:
            followers.append(OSNode(i))
    
    return leader, followers

def start(args):
    leader, followers = get_orderers()
    while True:
        start_time = helpers.startStopwatch()
        # 1. The leader assembles transactions
        block: Block = leader.assemble_transactions()
        
        elapsed = helpers.stopStopwatch(start_time, secs=True)
        if elapsed < 2:
            time.sleep(2 - elapsed)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Start ordering service simulation.')
    args = parser.parse_args()
    # start(args)