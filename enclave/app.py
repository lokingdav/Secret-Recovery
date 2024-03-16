from skrecovery.helpers import parse_json
from enclave.response import EnclaveRes
from enclave.requests import EnclaveReqType, StoreReq, RetrieveReq, RemoveReq, RecoverReq, VerifyCiphertextReq, TEEReq

def parse_req(req) -> StoreReq | RetrieveReq | RemoveReq | RecoverReq | VerifyCiphertextReq:
    if req['type'] == EnclaveReqType.STORE.value:
        return StoreReq(req)
    elif req['type'] == EnclaveReqType.RETRIEVE.value:
        return RetrieveReq(req)
    elif req['type'] == EnclaveReqType.REMOVE.value:
        return RemoveReq(req)
    elif req['type'] == EnclaveReqType.RECOVER.value:
        return RecoverReq(req)
    elif req['type'] == EnclaveReqType.VERIFY_CIPHERTEXT.value:
        return VerifyCiphertextReq(req)

def TEE(req: dict | str) -> dict | str:
    if type(req) == str:
        req = parse_json(req)
        
    req: TEEReq = parse_req(req)
    res: EnclaveRes = req.process_req()
    return res.serialize()