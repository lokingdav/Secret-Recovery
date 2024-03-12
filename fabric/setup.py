import json
from fabric import transaction
from skrecovery import sigma, config, database

filename = 'fabric-keys.json'

class MSP:
    _id: str = 'fabric-keys'
    peers: list[dict] = []
    orderers: list[dict] = []
    
    def save(self):
        database.save_fabric_keys(self.to_dict())
    
    def to_dict(self):
        return {
            '_id': self._id,
            'peers': self.peers,
            'orderers': self.orderers
        }
    
    @staticmethod
    def from_dict(data: dict) -> 'MSP':
        msp = MSP()
        msp.peers = data['peers']
        msp.orderers = data['orderers']
        return msp
        
def keygen(count):
    data = []
    for i in range(count):
        sk, vk = sigma.keygen()
        sk, vk = sigma.stringify(sk), sigma.stringify(vk)
        data.append({'sk': sk, 'vk': vk})
    return data

def load_MSP():
    data = database.load_fabric_keys()
    msp: MSP = MSP()
    msp.from_dict(data)
    return msp

def main():
    existing_data = database.load_fabric_keys()
    
    if existing_data:
        choice = input('Fabric keys already exist. Overwrite? (y/n): ')
        if choice.lower() != 'y':
            return
        
    msp: MSP = MSP()
    msp.peers = keygen(config.NUM_PEERS)
    msp.orderers = keygen(config.NUM_ORDERERS)
    msp.save()
    
if __name__ == '__main__':
    main()