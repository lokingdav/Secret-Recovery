import json
from skrecovery import sigma, config

filename = 'fabric-keys.json'

class MSP:
    peers: list[tuple[str, str]] = []
    orderers: list[tuple[str, str]] = []

def main():
    data = {
        'peers': keygen(config.NUM_PEERS),
        'orderers': keygen(config.NUM_ORDERERS),
    }
    with open(filename, 'w') as file:
        json.dump(data, file, indent=4)
        
        
def keygen(count):
    data = []
    for i in range(config.NUM_PEERS):
        sk, pk = sigma.keygen()
        data.append(sigma.export_keys(sk, pk))
    return data

def load_MSP():
    policies: MSP = None
    with open('fabric-keys.json', 'r') as file:
        data = json.load(file)
        policies = MSP()
        policies.peers = [sigma.parse_keys(key, imp = False) for key in data['peers']]
        policies.orderers = [sigma.parse_keys(key, imp = False) for key in data['orderers']]
    return policies

if __name__ == '__main__':
    main()