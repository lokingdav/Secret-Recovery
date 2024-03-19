import enclave.storage as storage, json
from crypto import sigma, ec_group, ciphers
from skrecovery.client import PermInfo
from skrecovery import helpers
from enum import Enum
from enclave.response import EnclaveRes

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
        
        self.pk = ec_group.import_point(req['params']['pk'])
        self.ctx = req['params']['ctx']
        self.req = req['params']['req']
        self.perm = req['params']['perm']
        self.perm_info = PermInfo.from_dict(req['params']['perm']['open']['perm_info'])
        self.retK = storage.get_retK(sigma.stringify(self.perm_info.vkc))
        
    def process_req(self) -> EnclaveRes:
        self.benchmark.reset().start()
        res: EnclaveRes = EnclaveRes()
        res.req_type = EnclaveReqType.RECOVER.value
        
        try:
            req: dict = { 'action': 'recover', 'pk': self.pk}
            valid_req: bool = helpers.stringify(req) == helpers.stringify(self.req)
            if self.verify_perm() is False or valid_req is False:
                raise Exception("Invalid permissions")
            
            ctx: ciphers.AESCtx = ciphers.AESCtx.from_string(self.ctx)
            plaintext: bytes = ciphers.aes_dec(self.retK, ctx)
            plaintext: dict = helpers.parse_json(plaintext.decode('utf-8'))
            
            perm_info_matched: bool = helpers.stringify(plaintext['perm_info']) == helpers.stringify(self.perm_info.to_dict())
            other_check: bool = plaintext['req'] is None and plaintext['res'] is None and plaintext['perm'] is None
            if not perm_info_matched or not other_check:
                raise Exception("Invalid permissions")
            
            data: dict = {
                'data': plaintext['data'].decode('utf-8') if isinstance(plaintext['data'], bytes) else plaintext['data'],
                'perm_info': self.perm_info.to_dict(),
                'req': self.req,
                'perm': self.perm,
            }
            ctx: ciphers.RSACtx = ciphers.rsa_enc(self.pk, data=data)
            res.ctx_fin = ctx.to_string()
        except Exception as e:
            res.error = str(e)
            
        res.time_taken = self.benchmark.end().total(short=False)
        return res
        
    def verify_perm(self) -> bool:
        pass