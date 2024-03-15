from crypto import sigma
from skrecovery import helpers
import random
import json
import os, pickle


miners_file = 'miners.pkl'
miners = {}
num_miners = 100
trnx = None

def init():
    global miners, trnx
    
    if os.path.exists(miners_file):
        with open(miners_file, 'rb') as file:
            tempdata = pickle.load(file)
            for vk in tempdata:
                pk = sigma.import_pub_key(vk)
                sk = sigma.import_priv_key(tempdata[vk])
                miners[vk] = (sk, pk)
    else:
        tempdata = {}
        for i in range(num_miners):
            sk, vk = sigma.keygen()
            miners[sigma.stringify(vk)] = (sk, vk)
            sk, vk = sigma.stringify(sk), sigma.stringify(vk)
            tempdata[vk] = sk
            
        with open(miners_file, 'wb') as file:
            pickle.dump(tempdata, file)
        
    with open('tx.json', 'r') as file:
        trnx = json.load(file)

def create_block(prev: str, transactions: list = []):
    num_trnx = 100 # random.randint(1, 1000)
    
    if len(transactions) == 0:
        num_trnx = num_trnx - len(transactions)
        data = transactions
        
    data = transactions + [trnx for _ in range(num_trnx)]
    data = [helpers.stringify(tx) for tx in data]
    # print(data[0])
    sigs = []
    
    for vk in miners:
        sig = sigma.sign(miners[vk][0], helpers.stringify(data))
        sigs.append((sig, miners[vk][1]))
        
    return {
        'data': data, 
        'prev_hash': prev,
        'hash': helpers.hash256(helpers.stringify(data) + prev),
        'sigs': sigs
    }

def create_window(n):
    blocks = []
    prev_hash = '0'
    for i in range(n):
        block = create_block(prev_hash)
        blocks.append(block)
        prev_hash = block['hash']
        
    return blocks

def validate_block(block):
    data = helpers.stringify(block['data'])
    valid_count = 0

    for i in range(len(block['sigs'])):
        sig, vk = block['sigs'][i]
        if sigma.stringify(vk) in miners and sigma.verify(vk, data, sig):
            valid_count += 1
        if valid_count > num_miners // 2:
            return True
        
    return False

def validate_window(blocks):
    for i in range(len(blocks)):
        if not validate_block(blocks[i]):
            return False
        
        if i > 0 and blocks[i]['prev_hash'] != blocks[i-1]['hash']:
            return False
        
    return True