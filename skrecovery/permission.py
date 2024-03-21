from fabric.transaction import Transaction, TxHeader, Signer, TxType
from fabric.block import Block

class Permission:
    def __init__(self) -> None:
        self.open_tx: Transaction = None
        self.tx_reg: Transaction = None
        self.server_regtx: Transaction = None
        self.client_regtx: Transaction = None
        self.chal_window_c: list[Block] = []
        self.com_window_req: list[Block] = []
        self.chal_window_req: list[Block] = []
        
    def to_dict(self) -> dict:
        return {
            'open_tx': self.open_tx.to_dict(),
            'tx_reg': self.tx_reg.to_dict(),
            'server_regtx': self.server_regtx.to_dict(),
            'client_regtx': self.client_regtx.to_dict(),
            'chal_window_c': [block.to_dict() for block in self.chal_window_c],
            'com_window_req': [block.to_dict() for block in self.com_window_req],
            'chal_window_req': [block.to_dict() for block in self.chal_window_req]
        }
        
    @staticmethod
    def from_dict(data: dict):
        perm = Permission()
        perm.open_tx = Transaction.from_dict(data['open_tx'])
        perm.tx_reg = Transaction.from_dict(data['tx_reg'])
        perm.server_regtx = Transaction.from_dict(data['server_regtx'])
        perm.client_regtx = Transaction.from_dict(data['client_regtx'])
        perm.chal_window_c = [Block.from_dict(block) for block in data['chal_window_c']]
        perm.com_window_req = [Block.from_dict(block) for block in data['com_window_req']]
        perm.chal_window_req = [Block.from_dict(block) for block in data['chal_window_req']]
        return perm