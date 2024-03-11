from skrecovery import sigma
from fabric import ledger, transaction

def test_ledger_post():
    sk, vk = sigma.keygen()
    proposal: dict = {'key': 'value'}
    vk_str: str = sigma.stringify(vk)
    signature: sigma.Signature = sigma.sign(sk, proposal)
    tx_signature: transaction.TxSignature = transaction.TxSignature(vk_str, signature)
    ledger.post(transaction.TxType.FAKE, proposal, tx_signature)
    

test_ledger_post()