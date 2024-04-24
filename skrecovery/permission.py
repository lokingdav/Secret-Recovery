from crypto import sigma
from fabric.transaction import Transaction, TxHeader, Signer, TxType
from fabric.block import Block

class PermInfo:
    def __init__(self) -> None:
        self.t_open: int = None
        self.t_chal: int = None
        self.t_wait: int = None
        self.vkc: sigma.PublicKey = None
        self.vks: sigma.PublicKey = None
    
    def to_dict(self):
        return {
            't_open': self.t_open,
            't_wait': self.t_wait,
            't_chal': self.t_chal,
            'vkc': sigma.stringify(self.vkc),
            'vks': sigma.stringify(self.vks)
        }
        
    @staticmethod
    def from_dict(data: dict):
        perm_info = PermInfo()
        perm_info.t_open = int(data.get('t_open'))
        perm_info.t_wait = int(data['t_wait'])
        perm_info.t_chal = int(data['t_chal'])
        perm_info.vkc = sigma.import_pub_key(data['vkc'])
        perm_info.vks = sigma.import_pub_key(data['vks'])
        return perm_info

class Permission:
    def __init__(self) -> None:
        self.open_tx: Transaction = None
        self.tx_reg: Transaction = None
        self.server_regtx: Transaction = None
        self.client_regtx: Transaction = None
        self.com_window_req: list[Block] = []
        self.chal_window_req: list[Block] = []
        self.tx_open_block_number: int = None
        
    def to_dict(self) -> dict:
        return {
            'open_tx': self.open_tx.to_dict(),
            'tx_reg': self.tx_reg.to_dict(),
            'server_regtx': self.server_regtx.to_dict(),
            'client_regtx': self.client_regtx.to_dict(),
            'tx_open_block_number': self.tx_open_block_number,
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
        perm.tx_open_block_number = int(data['tx_open_block_number'])
        perm.com_window_req = [Block.from_dict(block) for block in data['com_window_req']]
        perm.chal_window_req = [Block.from_dict(block) for block in data['chal_window_req']]
        return perm