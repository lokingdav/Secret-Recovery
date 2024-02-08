from . import helpers, sigma
import random
import json
import os, pickle


miners_file = 'miners.pkl'
miners = {}
num_miners = 2
sample_data = None

def init():
    global miners, sample_data
    
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
        sample_data = json.load(file)

def create_block(prev: str):
    num_trnx = random.randint(1, 1000)
    data = [sample_data for _ in range(num_trnx)]
    sigs = []
    
    for vk in miners:
        sig = sigma.sign(miners[vk][0], json.dumps(data))
        sigs.append((sig, miners[vk][1]))
        
    return {
        'data': data, 
        'prev_hash': prev,
        'hash': helpers.hash256(json.dumps(data) + prev),
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
    data = json.dumps(block['data'])
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