import json

from ..crypto import commitment, sigma
from . import ledger, helpers
from .server import server as Server
from .client import client as Client
from multiprocessing import Pool

num_processes = 10
servers, clients = [], []

def init():
    ledger.setup()

def register(data):
    register_servers(int(data['num-servers']))
    register_clients(data['clients'])

def register_servers(num_servers):
    global servers
    cid = ledger.get_cid(str)
    for i in range(num_servers):
        print(f"Registering server {i}")
        serv = Server(id=i)
        serv.register(cid=cid)
        servers.append(serv)
        
def register_clients(data):
    global clients
    for server_id in data:
        start, end = get_range(data[server_id])
        server_id = int(server_id)
        for i in range(start, end):
            print(f"Registering client {i} to server {server_id}")
            # set client and server to register to
            client, server = Client(id=i), servers[server_id]
            # Register client to server on ledger
            block = client.register(cid=server.regb.cid, bid=server.regb.idx)
            
            # Send block to server and receive signature
            sig = server.register_client(block)
            
            if sig is None:
                continue
            
            if not client.verify_registration(sig, block.data):
                raise Exception("Registration failed")
            
            clients.append(client)
             
def generate_permission(data):
    party_type, party_idx = data['party'].split(':')
    party_idx = int(party_idx)
    party = clients[party_idx] if party_type == 'client' else servers[party_idx]
    server = servers[data['server-idx']]
    client_perm_info = clients[data['perm-info-client-idx']].perm_info
    req = data['req']
    
    # commit and post commit to ledger
    message = helpers.stringify({
        'perm_info': client_perm_info,
        'server': server.id,
        'req': req,
    })
    com, secret = commitment.commit(message)
    block_data = helpers.stringify({
        'type': ledger.Block.TYPE_REQUEST,
        'com': commitment.export_com(com),
        'cmd-id': str(data['cmd-id']),
    })
    block: ledger.Block = ledger.post(data=block_data, cid=server.cid)
    
    # open commitment and post opening to ledger
    block_data = helpers.stringify({
        'type': ledger.Block.TYPE_REQUEST,
        'open': commitment.export_secret(secret),
        'cmd-id': str(data['cmd-id']),
    })
    ledger.post(data=block_data, cid=block.cid)

def client_accept_deny_permission(client_idx, data):
    pass

def server_accept_deny_permission(server_idx, data):
    pass

def on_seeing_tx_com_open(data):
    party_type, party_idx = data['party'].split(':')
    action, cmd_id = data['action'].split(':')
    data['action'], data['action-cmd-id'] = cmd_id
    
    if party_type == 'client':
        client_accept_deny_permission(int(party_idx), data)
    elif party_type == 'server':
        server_accept_deny_permission(int(party_idx), data)
    else:
        raise Exception(f"Invalid party type: {data}")
    
def run_sim_seq(data):
    for cmd in data:
        if cmd['type'] == 'gen_perms':
            generate_permission(cmd)
        elif cmd['type'] == 'see_tx_com_open':
            on_seeing_tx_com_open(cmd)
        else:
            raise Exception("Invalid simulation sequence type")
    
def simulate(env):
    envdata = json.loads(open(env).read())
    if 'register' not in envdata:
        raise Exception("No registration data found")
    register(envdata['register'])
    
    if 'sim-seq' not in envdata:
        raise Exception("No simulation sequence found")
    run_sim_seq(envdata['sim-seq'])

def get_range(args):
    start, end = 0, 0
    args = args.split(':')
    if len(args) == 2:
        start, end = args[0], args[1]
    else:
        start = args[0]
        end = start
        
    return (int(start), int(end))