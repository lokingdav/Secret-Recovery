import json
import hashlib
from . import sigma
from . import store

def hash256(data: str):
    return hashlib.sha256(data.encode()).hexdigest()

def setup(key):
    data = store.find(key)
    priv_k, pub_k, t_open, t_chal = None, None, None, None
    
    if data:
        data = json.loads(data)
        t_open, t_chal = data['t'].split(':')
        priv_k, pub_k = sigma.parse_keys(data['keys'])
    else:
        t_open, t_chal = 5, 5
        priv_k, pub_k = sigma.keygen()
        data = {'t': f'{t_open}:{t_chal}', 'keys': f'{priv_k}:{pub_k}'}
        store.save(key, json.dumps(data))
        
    return (priv_k, pub_k, t_open, t_chal)
