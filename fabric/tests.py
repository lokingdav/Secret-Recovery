import json
from crypto import sigma
from fabric.block import Block
from skrecovery import database
from skrecovery.helpers import Benchmark, wait
from fabric import ledger, transaction

def create_tx():
    sk, vk = sigma.keygen()
    data: dict = {'key': 'hello world!'}
    vk_str: str = sigma.stringify(vk)
    signature: sigma.Signature = sigma.sign(sk, data)
    tx_signature: transaction.Signer = transaction.Signer(vk_str, signature)
    tx: transaction.Transaction = ledger.post(transaction.TxType.FAKE.value, data, tx_signature)
    return tx

def test_ledger_post():
    tx: transaction.Transaction = create_tx()
    txstr = tx.to_string()

def test_tx_serialization():
    tx1 = create_tx()
    tx1str = tx1.to_string()
    tx2 = transaction.Transaction.from_dict(json.loads(tx1str))
    tx2str = tx2.to_string()
    assert tx1str == tx2str
    
def test_block_serialization():
    block: Block = Block(init=False)
    tx = create_tx()
    block.data.add_tx(tx.to_string())
    block.metadata.bitmap = {'hello': 'world'}
    bdict = block.to_dict()
    bdict2: Block = Block.from_dict(bdict)
    bdict2 = bdict2.to_dict()
    assert bdict == bdict2
    
def verify_blockchain():
    chain: list[Block] = database.get_chain()
    num_blocks = len(chain)
    
    for i in range(0, num_blocks):
        block: Block = Block.from_dict(chain[i])
        assert block.to_dict() == chain[i]
        assert block.verify()
        
        if i == 0:
            continue
        prev_block: Block = Block.from_dict(chain[i - 1])
        assert block.verify_previous_block(prev_block)
        
        print(f'Verified block id: {chain[i]["_id"]}, {i+1} of {num_blocks}')
    print('All blocks verified!')
        
        
if __name__ == '__main__':
    pass