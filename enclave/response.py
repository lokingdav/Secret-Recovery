from crypto import sigma

class EnclaveRes:
    def __init__(self) -> None:
        self.req_type = None
        self.payload = {}
        self.time_taken = 0
        self.is_removed = False
        self.is_valid_ctx = False
        self.signature = None
        self.error = None
    
    def verify(self, vk: str | sigma.PublicKey):
        return True # todo: verify attestation
    
    def serialize(self):
        if self.error is not None:
            return {
                'type': self.req_type,
                'error': self.error
            }
            
        return {
            'type': self.req_type,
            'signature': sigma.stringify(self.signature),
            'payload': self.payload,
            'is_valid_ctx': self.is_valid_ctx,
            'is_removed': self.is_removed,
            'time_taken': self.time_taken,
            'error': self.error
        }
        
    def sign(self, sk: str | sigma.PrivateKey):
        self.signature = sigma.sign(sk, self.payload)

    @staticmethod
    def deserialize(data: dict):
        res = EnclaveRes()
        res.req_type = data.get('type', None)
        res.payload = data.get('payload', {})
        res.is_removed = bool(data.get('is_removed', False))
        res.is_valid_ctx = bool(data.get('is_valid_ctx', False))
        res.signature = sigma.import_signature(data.get('signature')) if data.get('signature') is not None else None
        res.time_taken = data.get('time_taken', 0)
        res.error = data.get('error', None)
        return res
    
    @staticmethod
    def error(code: int, message: str) -> 'EnclaveRes':
        res = EnclaveRes()
        res.error = {
            'code': code,
            'message': message
        }
        return res
