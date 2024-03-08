import time
import random
import multiprocessing

num_processes = 4

def worker():
    print(f"Starting worker {multiprocessing.current_process().name}")
    try:
        while True:
            # Your repeated task here
            sleeptime = random.uniform(0, 1.5)
            time.sleep(sleeptime)  # Example task: just sleep for 1 second
            print(f"Worker {multiprocessing.current_process().name} is working")
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

if __name__ == "__main__":
    processes = create_workers()
    # The main process continues doing other stuff
    try:
        while True:
            time.sleep(0.1)  # Main process does something else
    except KeyboardInterrupt:
        stop_workers(processes)
