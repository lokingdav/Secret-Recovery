import argparse, random, pickle
from skrecovery.client import Client
from skrecovery.server import Server
from skrecovery.helpers import Benchmark, startStopwatch, endStopwatch
from fabric.block import Block
from fabric.transaction import Transaction
from fabric import noise_simulation
from experiments.misc import get_client, get_cloud
from experiments.store import main as store_script, client_secret_info
from fabric import ordering_service
from skrecovery import config, database

BLK_SEEDS = []
START_BLK_ID = -1

def rand_block_data():
    return BLK_SEEDS[random.randint(0, len(BLK_SEEDS)-1)]

def init():
    global BLK_SEEDS
    # load seeded transactions from pickle file
    try:
        with open('experiments/seeded_blks.pkl', 'rb') as f:
            BLK_SEEDS = pickle.load(f)
    except EOFError:
        print("Pickle file is empty or corrupted. Creating new seeded blocks.")
        BLK_SEEDS = []
        
    if BLK_SEEDS:
        return BLK_SEEDS
    else:
        print("Creating seeded blocks")
        for _ in range(config.T_CHAL):
            print("Creating block", _+1)
            BLK_SEEDS.append(seed_transactions())
            
        with open('experiments/seeded_blks.pkl', 'wb') as f:
            pickle.dump(BLK_SEEDS, f)

def seed_transactions(transactions: list[Transaction] = []):
    txs = []
    total = 0
    while True:
        tx = noise_simulation.post_fake_tx(send_tos=False)
        if total + tx.size_in_kb > config.PREFERRED_MAX_BLOCK_SIZE_KB:
            break
        total += tx.size_in_kb
        txs.append(tx.to_dict())
    return txs + transactions

def simulate(tx_com: dict, tx_open: dict, t_open: int, t_chal: int, t_wait: int) -> list[dict]:
    global START_BLK_ID
    
    if not isinstance(tx_com, dict) or not isinstance(tx_open, dict):
        raise Exception('tx_com and tx_open must be dictionaries.')
    
    print("Simulating blockchain for challenge window")
    prev_block = database.get_latest_block()
    START_BLK_ID = prev_block['_id']
    blocks = []
    leader, followers = ordering_service.get_orderers()
    
    print('Start from block:', prev_block['_id'])
    # Create block for commit transaction
    blk1 = ordering_service.begin_consensus(
        pending_txs=rand_block_data() + [tx_com],
        leader=leader, 
        followers=followers,
        prev_block=prev_block,
        save=False
    ).to_dict()
    blocks.append(blk1)
    prev_block = blk1
    
    # Create block for open transaction
    _blks = [False for _ in range(t_open - 1)]
    _blks.append(True)
    random.shuffle(_blks) # shuffle position so that block for t_open appears within t_open window
    
    for i, _blk in enumerate(_blks):
        txs = rand_block_data()
        txs = txs + [tx_open] if _blk else txs
        blk2 = ordering_service.begin_consensus(
            pending_txs=txs, 
            leader=leader, 
            followers=followers,
            prev_block=prev_block,
            save=False
        ).to_dict()
        blocks.append(blk2)
        prev_block = blk2
        print(f"\rOpen window: Created block {i+1}/{len(_blks)}", end='')
    
    # Skip wait window, simulate time by updating block number
    prev_block['_id'] = prev_block['_id'] + t_wait
    prev_block['header']['number'] = prev_block['_id']
    print("")
    
    # Create blocks for the challenge time
    for i in range(t_chal):
        blk = ordering_service.begin_consensus(
            pending_txs=BLK_SEEDS[i], 
            leader=leader, 
            followers=followers,
            prev_block=prev_block,
            save=False
        ).to_dict()
        blocks.append(blk)
        prev_block = blk
        print(f"\rChallenge window: Created block {i+1}/{t_chal}", end='')
    
    print("\nSaving blocks to database")
    database.insert("ledgers", blocks)
    
def clean():
    global START_BLK_ID
    if START_BLK_ID > -1:
        database.delete_blocks_after(START_BLK_ID)
        START_BLK_ID = -1
