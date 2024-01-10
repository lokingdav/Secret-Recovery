import time
import random
import json
from . import ledger, sigma
from .server import server as Server
from .client import client as Client
from multiprocessing import Pool

num_processes = 10
servers, clients = [], []

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
    print(data)
     
def run_sim_seq(data):
    for cmd in data:
        if cmd['type'] == 'gen_perms':
            generate_permission(cmd)
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