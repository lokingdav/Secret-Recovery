import enclave.storage as storage, json
from crypto import sigma, ec_group, ciphers
from skrecovery.client import PermInfo
from skrecovery.enclave import EnclaveReqType, EnclaveRes
from skrecovery import helpers

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
    perm_info: PermInfo = None
    point: ec_group.Point = None
    vkc: sigma.PublicKey = None
    
    def __init__(self, req: dict) -> None:
        self.validate_req(req)
        self.perm_info = PermInfo.from_dict(req['params']['perm_info'])
        self.point = ec_group.import_point(req['params']['point'])
        self.vkc = sigma.import_pub_key(req['params']['vkc'])
        
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
        return res
        
class VerifyCiphertextReq(TEEReq):
    perm_info: PermInfo = None
    ctx: str = None
    
    def __init__(self, req: dict) -> None:
        self.validate_req(req)
        if req['type'] != EnclaveReqType.VERIFY_CIPHERTEXT.value:
            raise Exception("Invalid request type")
        self.perm_info = PermInfo.from_dict(req['params']['perm_info'])
        self.ctx = req['params']['ctx']
        
    def process_req(self) -> EnclaveRes:
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
        return res
    
class RetrieveReq(TEEReq):
    def __init__(self, req: dict) -> None:
        pass
    
class RemoveReq(TEEReq):
    def __init__(self, req: dict) -> None:
        pass
    
class RecoverReq(TEEReq):
    def __init__(self, req: dict) -> None:
        pass