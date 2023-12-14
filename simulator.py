import time
import random
from htras import ledger, sigma
from htras.server import server as Server
from htras.client import client as Client
from multiprocessing import Pool

num_processes = 10
servers, clients = [], []
num_servers, num_clients = 1, 1

def register_servers():
    global servers
    for i in range(num_servers):
        serv = Server(id=i)
        serv.register(cid=i)
        servers.append(serv)
        
def register_clients():
    global clients
    for i in range(num_clients):
        # set client and server to register to
        client, server = Client(id=i), servers[0]
        # Register client to server on ledger
        block = client.register(cid=server.regb.cid, idx=server.regb.idx)
        
        # Send block to server and receive signature
        sig = server.register_client(block)
        
        # Verify signature
        if not client.verify_registration(sigma.import_signature(sig), block.data):
            raise Exception("Registration failed")
        
        clients.append(client)
        
def run_client(client):
    while True:
        time.sleep(random.randint(1, 10))
        

def main():
    register_servers()
    register_clients()
    
    pool = Pool(processes=num_processes)
    pool.map(run_client, clients)