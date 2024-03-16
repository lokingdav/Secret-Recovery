from crypto import sigma

class EnclaveRes:
    def __init__(self) -> None:
        self.req_type = None
        self.payload = {}
        self.time_taken = 0
        self.is_removed = False
        self.is_valid_ctx = False
        self.signature = None
    
    def verify(self, vk: str | sigma.PublicKey):
        return True # todo: sigma.verify(vk, self.payload, self.signature)
    
    def serialize(self):
        return {
            'type': self.req_type,
            'signature': sigma.stringify(self.signature),
            'payload': self.payload,
            'is_valid_ctx': self.is_valid_ctx,
            'is_removed': self.is_removed
        }
        
    def sign(self, sk: str | sigma.PrivateKey):
        self.signature = sigma.sign(sk, self.payload)

    @staticmethod
    def deserialize(data: dict):
        res = EnclaveRes()
        res.req_type = data['type']
        res.payload = data['payload']
        res.is_removed = bool(data['is_removed'])
        res.is_valid_ctx = bool(data['is_valid_ctx'])
        res.signature = sigma.import_signature(data['signature']) if data['signature'] is not None else None
        return res
