import traceback
from enum import Enum
from skrecovery import helpers
from fabric.block import Block
import enclave.storage as storage
import fabric.window as blockchain 
from enclave.response import EnclaveRes
from skrecovery.permission import Permission, PermInfo
from crypto import sigma, ec_group, ciphers, commitment
from fabric.transaction import Transaction, Signer, TxType

class EnclaveReqType(Enum):
    STORE = 'store'
    REMOVE = 'remove'
    RECOVER = 'recover'
    RETRIEVE = 'retrieve'
    VERIFY_CIPHERTEXT = 'verify_ciphertext'
    
class TEEReq:
    def validate_req(self, req: dict):
        if req is None or type(req) is not dict:
            raise Exception("Invalid request")
        
        if 'type' not in req:
            raise Exception("Invalid request: missing type field")
        
        if 'params' not in req or type(req['params']) is not dict:
            raise Exception("Invalid request: missing params field")
    
    def process_req(self) -> EnclaveRes:
        pass

class StoreReq(TEEReq):
    def __init__(self, req: dict) -> None:
        self.validate_req(req)
        self.perm_info = PermInfo.from_dict(req['params']['perm_info'])
        self.point = ec_group.import_point(req['params']['point'])
        self.vkc = sigma.import_pub_key(req['params']['vkc'])
        self.benchmark = helpers.Benchmark(name="store", filename=None)
        
    def validate_req(self, req: dict):
        super().validate_req(req)
        if req['type'] != EnclaveReqType.STORE.value:
            raise Exception("Invalid request type")
        
        params: dict = req['params']
        if 'perm_info' not in req['params'] or type(params['perm_info']) is not dict:
            raise Exception("Invalid request parameters: perm_info")
        if 'point' not in params or type(params['point']) is not str:
            raise Exception("Invalid request parameters: point")
        if 'vkc' not in params or type(params['vkc']) is not str:
            raise Exception("Invalid request parameters: vkc")
        
    def process_req(self) -> EnclaveRes:
        self.benchmark.reset().start()
        vk: str = sigma.stringify(self.vkc)
        discrete_log, point2 = ec_group.random_DH()
        retK: ec_group.Point = discrete_log * self.point
        storage.add_client(vk, retK)
        
        res: EnclaveRes = EnclaveRes()
        res.req_type = EnclaveReqType.STORE.value
        res.payload = {
            'c_point': ec_group.export_point(self.point),
            't_point': ec_group.export_point(point2),
            'vkc': vk
        }
        # todo: sign the response
        res.time_taken = self.benchmark.end().total(short=False)
        return res
        
class VerifyCiphertextReq(TEEReq):
    def __init__(self, req: dict) -> None:
        self.validate_req(req)
        if req['type'] != EnclaveReqType.VERIFY_CIPHERTEXT.value:
            raise Exception("Invalid request type")
        self.perm_info = PermInfo.from_dict(req['params']['perm_info'])
        self.ctx = req['params']['ctx']
        self.benchmark = helpers.Benchmark(name="verifyciphertext", filename=None)
        
    def process_req(self) -> EnclaveRes:
        self.benchmark.reset().start()
        vkc: str = sigma.stringify(self.perm_info.vkc)
        ctx: ciphers.AESCtx = ciphers.AESCtx.from_string(self.ctx)
        retK: ec_group.Point = storage.get_retK(vkc)
        plaintext: bytes = ciphers.aes_dec(bytes(retK), ctx)
        plaintext: dict = helpers.parse_json(plaintext.decode('utf-8'))
        
        valid_perm_info: bool = helpers.stringify(plaintext['perm_info']) == helpers.stringify(self.perm_info.to_dict())
        valid_req_perm: bool = plaintext['req'] is None and plaintext['res'] is None and plaintext['perm'] is None
        
        res: EnclaveRes = EnclaveRes()
        res.req_type = EnclaveReqType.VERIFY_CIPHERTEXT.value
        res.is_valid_ctx = valid_perm_info and valid_req_perm
        res.payload = {'stored': res.is_valid_ctx}
        # todo: sign the response
        
        res.time_taken = self.benchmark.end().total(short=False)
        return res
    
class RetrieveReq(TEEReq):
    def __init__(self, req: dict) -> None:
        pass
    
class RemoveReq(TEEReq):
    def __init__(self, req: dict) -> None:
        self.validate_req(req)
        if req['type'] != EnclaveReqType.REMOVE.value:
            raise Exception("Invalid request type")
        
        self.perm_info = PermInfo.from_dict(req['params']['perm_info'])
        self.signature = sigma.import_signature(req['params']['signature'])
        self.benchmark = helpers.Benchmark(name="remove", filename=None)
        
    def process_req(self) -> EnclaveRes:
        self.benchmark.reset().start()
        sig_payload: dict = {
            'action': 'remove',
            'perm_info': self.perm_info.to_dict()
        }
        if not sigma.verify(self.perm_info.vkc, sig_payload, self.signature):
            raise Exception("Invalid client signature for remove request")
        
        res: EnclaveRes = EnclaveRes()
        res.req_type = EnclaveReqType.REMOVE.value
        res.is_removed = storage.remove_client(sigma.stringify(self.perm_info.vkc))
        res.payload = {'removed': res.is_removed}
        # todo: sign the response
        res.time_taken = self.benchmark.end().total(short=False)
        return res
    
class RecoverReq(TEEReq):
    def __init__(self, req: dict) -> None:
        self.benchmark = helpers.Benchmark(name="recover", filename=None)
        self.validate_req(req)
        if req['type'] != EnclaveReqType.RECOVER.value:
            raise Exception("Invalid request type")
        
        print("Setting up recover request")
        self.ctx: str = req['params']['ctx']
        self.req: dict = req['params']['req']
        self.perm: Permission = Permission.from_dict(req['params']['perm'])
        self.pk = req['params']['pk'] # ciphers.RSAKeyPair.import_key(req['params']['pk'])
        self.perm_info: PermInfo = PermInfo.from_dict(req['params']['perm']['open_tx']['data']['message']['perm_info'])
        self.retK = storage.get_retK(sigma.stringify(self.perm_info.vkc))
        
    def process_req(self) -> EnclaveRes:
        self.benchmark.reset().start()
        res: EnclaveRes = EnclaveRes()
        res.req_type = EnclaveReqType.RECOVER.value
        
        try:
            print("Verifying recover request")
            req: dict = { 'action': 'recover', 'pk': self.pk}
            valid_req: bool = helpers.stringify(req) == helpers.stringify(self.req)
            if  valid_req is False:
                raise Exception("Invalid permissions")
            
            print("Verifying permissions")
            self.verify_perm() # raise exception if invalid permissions
            
            print("Decrypting ciphertext")
            ctx: ciphers.AESCtx = ciphers.AESCtx.from_string(self.ctx)
            plaintext: bytes = ciphers.aes_dec(self.retK, ctx)
            plaintext: dict = helpers.parse_json(plaintext.decode('utf-8'))
            
            print("Checking permissions")
            perm_info_matched: bool = helpers.stringify(plaintext['perm_info']) == helpers.stringify(self.perm_info.to_dict())
            other_check: bool = plaintext['req'] is None and plaintext['res'] is None and plaintext['perm'] is None
            if not perm_info_matched or not other_check:
                raise Exception("Invalid permissions")
            
            del self.perm
            
            data: dict = {
                'data': plaintext['data'].decode('utf-8') if isinstance(plaintext['data'], bytes) else plaintext['data'],
                'perm_info': self.perm_info.to_dict(),
            }
            
            print("Encrypting data with client's public key")
            pk = ciphers.RSAKeyPair.import_key(bytes.fromhex(self.pk))
            ctx: ciphers.RSACtx = ciphers.rsa_enc(pk, data=data)
            res.payload = {'ctx_fin': ctx.to_string()}
        except Exception as e:
            traceback.print_exc()
            res.error = str(e)
        
        print("Finishing recover request")
        res.time_taken = self.benchmark.end().total(short=False)
        return res
        
    def verify_perm(self) -> bool:
        perm_info_str: str = helpers.stringify(self.perm.client_regtx.data)
        perm_info_prime: str = helpers.stringify(self.perm.open_tx.data['message']['perm_info'])
        if perm_info_str != perm_info_prime:
            print("perm_info_str: ", perm_info_str)
            print("perm_info_prime: ", perm_info_prime)
            raise Exception("Invalid permissions: perm_info_str != perm_info_prime")
        
        req_str: str = helpers.stringify(self.req)
        open_prime: str = helpers.stringify(self.perm.open_tx.data)
        if req_str not in open_prime:
            raise Exception("Invalid permissions: req_str not in open_prime")
        
        if not self.perm.client_regtx.signature.verify(self.perm.client_regtx.data):
            raise Exception("Invalid permissions: client_regtx signature")
        
        # verify registration tx
        if not self.perm.tx_reg.signature.verify(self.perm.tx_reg.data):
            raise Exception("Invalid permissions: tx_reg signature")
        
        # verify window
        self.verify_windows()
        
        # Verify client registration
        authorization = Signer.from_dict(self.perm.tx_reg.data['authorization'])
        if not authorization.verify(self.perm.client_regtx.data, self.perm_info.vks):
            raise Exception("Invalid permissions: Server did not authorize registration")
        
        # check if server accepted/denied registration
        # tx_reg: Transaction = Transaction.from_dict(self.perm['tx_reg'])
        signer: Signer = Signer.from_dict(self.perm.tx_reg.data['authorization'])
        if not signer.verify(self.perm_info.to_dict()):
            raise Exception("Invalid permissions: server signature")
        
        self.check_com_opening()
        
    def verify_windows(self) -> bool:
        if not blockchain.verify_window(self.perm.com_window_req):
            raise Exception("Invalid permissions: com_window_req")
        if not blockchain.verify_window(self.perm.chal_window_req):
            raise Exception("Invalid permissions: chal_window_req")
    
    def check_com_opening(self):
        block, tx_com = blockchain.find_commitment_for_opening(
            window=self.perm.com_window_req, 
            tx_open=self.perm.open_tx,
            tx_open_block_number=self.perm.tx_open_block_number
        )
        if not tx_com or not block:
            raise Exception("Invalid permissions: tx_com or block")
        
        if not commitment.open_com(
            com=tx_com.data['com'], 
            msg=self.perm.open_tx.data['message'], 
            sec=self.perm.open_tx.data['opening']
        ):
            raise Exception("Invalid permissions: commitment verification failed")
        
        # check if client accepted/denied tx_open
        for block in self.perm.chal_window_req:
            for tx in block.data.transactions:
                if tx.get_type() == TxType.OPEN_RESPONSE.value and tx.data['perm_info'] == self.perm_info.to_dict():
                    if not tx.signature.verify(tx.data, self.perm_info.vkc):
                        raise Exception("Invalid permissions: signature verification failed")
                    if tx.data['action'] == 'denied':
                        raise Exception("Invalid permissions: tx_open not denied")
        
        blocks: list[tuple[Block, Transaction]] = blockchain.find_other_openings(
            window=self.perm.chal_window_req, 
            tx_open=self.perm.open_tx
        )
        
        if not blocks:
            return True
        
        for block, tx_open_prime in blocks:
            block_com, tx_com = blockchain.find_commitment_for_opening(
                window=self.perm.com_window_req,
                tx_open=tx_open_prime,
                tx_open_block_number=block.get_number()
            )
            if not block_com:
                continue
            is_valid_opening = commitment.open_com(
                com=tx_com.data['com'],
                msg=tx_open_prime.data['message'],
                sec=tx_open_prime.data['opening']
            )
            
            distance = block.get_number() - block_com.get_number()
            
            if is_valid_opening and distance <= self.perm.open_tx.data['message']['perm_info']['t_open']:
                raise Exception("Invalid permissions: invalid opening")
        
        check1: bool = len(self.perm.com_window_req) == self.perm_info.t_open + 1 # buffer
        check2: bool = len(self.perm.chal_window_req) == self.perm_info.t_chal
        if not check1 or not check2:
            raise Exception("Invalid permissions: check1 or check2")
        
        return True
        