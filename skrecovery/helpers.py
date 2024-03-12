import json
import time
import hashlib
import secrets
from . import sigma
from . import store

def hash256(data: str):
    data = data.encode() if type(data) == str else data
    return hashlib.sha256(data).hexdigest()

def stringify(data):
    if type(data) == str:
        return data
    return json.dumps(data)

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
        data = {'t': f'{t_open}:{t_chal}', 'keys': f'{sigma.stringify(priv_k)}:{sigma.stringify(pub_k)}'}
        store.save(key, json.dumps(data))
        
    return (priv_k, pub_k, t_open, t_chal)

def startStopwatch():
    return time.perf_counter()

def endStopwatch(test_name, start, numIters, silent=False):
    end_time = time.perf_counter()
    total_dur_ms = (end_time - start) * 1000
    avg_dur_ms = total_dur_ms / numIters

    if not silent:
        print("\n%s\nTotal: %d runs in %0.1f ms\nAvg: %fms"
            % (test_name, numIters, total_dur_ms, avg_dur_ms))
        
    return test_name, total_dur_ms, avg_dur_ms

def stopStopwatch(start, secs=False):
    end_time = time.perf_counter()
    
    if secs:
        return end_time - start
    
    return (end_time - start) * 1000

def random_bytes(n, hex=False):
    d = secrets.token_bytes(n)
    if hex:
        return d.hex()
    return d

def update_csv(file, line, header = None):
    with open(f'results/{file}', 'a') as f:
        # Write header if file is empty
        if f.tell() == 0 and header:
            f.write(header + '\n')
            
        f.write(line + '\n')
        
def create_csv(file, header, mode = 'a'):
    with open(f'results/{file}', mode) as f:
        if f.tell() == 0:
            f.write(header + '\n')
            
def get_number(prompt, default):
    while True:
        try:
            return int(input(prompt) or default)
        except ValueError:
            print("Invalid input. Please enter a number.")

            