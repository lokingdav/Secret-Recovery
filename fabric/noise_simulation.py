from crypto import sigma
from fabric import ledger
from fabric.transaction import Transaction, TxType, Signer
from skrecovery import helpers, config
import time, random, argparse, multiprocessing, sys, base64

num_processes = 1

def post_fake_tx(send_tos: bool = True):
    sk, vk = sigma.keygen()
    size = random.randint(1, 10 * 1024) # random size between 1B and 10KB
    data: dict = {'fake': base64.b64encode(helpers.random_bytes(size)).decode()}
    vk_str: str = sigma.stringify(vk)
    signature: sigma.Signature = sigma.sign(sk, data)
    tx_signature: Signer = Signer(vk_str, signature)
    tx: Transaction = ledger.post(TxType.FAKE.value, data, tx_signature, send_tos=send_tos)
    return tx

def sleep_random():
    sleeptime = random.uniform(0, 200 / 1000) # random sleep time between 0 and 25 ms
    print('Sleeping for', sleeptime, 'seconds')
    time.sleep(sleeptime)
    
            
def worker():
    print(f"Starting worker {multiprocessing.current_process().name}")
    while True:
        try:
            # start = helpers.startStopwatch()
            tx: Transaction = post_fake_tx()
            # end = helpers.stopStopwatch(start)
            # print(f"Worker {multiprocessing.current_process().name} took {end} ms to post tx {tx.get_id()}")
            sleep_random()
            print(f"Worker {multiprocessing.current_process().name} posted tx {tx.get_id()}")
        except Exception as e:
            print(f"Worker {multiprocessing.current_process().name} received {e}")

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
        
    