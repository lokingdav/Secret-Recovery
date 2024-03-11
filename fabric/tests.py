from skrecovery import sigma, helpers
from fabric import ledger, transaction

def create_tx():
    sk, vk = sigma.keygen()
    proposal: dict = {'key': 'hello world!'}
    vk_str: str = sigma.stringify(vk)
    signature: sigma.Signature = sigma.sign(sk, proposal)
    tx_signature: transaction.TxSignature = transaction.TxSignature(vk_str, signature)
    tx: transaction.Transaction = ledger.post(transaction.TxType.FAKE, proposal, tx_signature)
    return tx

def test_ledger_post():
    tx: transaction.Transaction = create_tx()
    txstr = tx.to_string()
    print(txstr)
    print(tx.size_in_memory())
    print(tx.size_of_exported_data())    

def test_tx_serialization():
    tx1 = create_tx()
    tx1str = tx1.to_string()
    tx2 = transaction.Transaction.from_string(tx1str)
    
    tx2str = tx2.to_string()
    
    assert tx1str == tx2str
    
    print('Size in bytes')
    print('tx1:', tx1.size())
    print('tx2:', tx2.size())
    
    
test_tx_serialization()