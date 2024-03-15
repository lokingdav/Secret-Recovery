from crypto import sigma
from fabric import ledger
from fabric.transaction import Transaction, TxType, Signer
from skrecovery import helpers
import time, random, argparse, multiprocessing, sys, base64

num_processes = 4

def post_fake_tx():
    sk, vk = sigma.keygen()
    proposal: dict = {'fake': base64.b64encode(helpers.random_bytes(256)).decode()}
    vk_str: str = sigma.stringify(vk)
    signature: sigma.Signature = sigma.sign(sk, proposal)
    tx_signature: Signer = Signer(vk_str, signature)
    tx: Transaction = ledger.post(TxType.FAKE.value, proposal, tx_signature)
    return tx

def worker():
    print(f"Starting worker {multiprocessing.current_process().name}")
    try:
        while True:
            tx: Transaction = post_fake_tx()
            sleeptime = random.uniform(0, 1.5)
            time.sleep(sleeptime)
            print(f"Worker {multiprocessing.current_process().name} posted tx {tx.get_id()} and slept for {sleeptime} seconds")
    except KeyboardInterrupt:
        print(f"Stopping worker {multiprocessing.current_process().name}")

def create_workers():
    processes = []
    for _ in range(num_processes):
        p = multiprocessing.Process(target=worker)
        p.start()
        processes.append(p)
    return processes

def stop_workers(processes):
    for p in processes:
        p.terminate()
        p.join()

def simulation(args):
    processes = create_workers()
    # The main process continues doing other stuff
    try:
        while True:
            time.sleep(0.1)  # Main process does something else
    except KeyboardInterrupt:
        stop_workers(processes)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='World simulation')
    parser.add_argument('-w', '--world', action='store_true', help='Run entire simulation', required=False, default=False)
    args = parser.parse_args()
    
    if args.world:
        simulation(args)
        
    