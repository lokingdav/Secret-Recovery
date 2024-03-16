import json, time, hashlib, secrets

class Benchmark:
    name: str = None
    entries: list = []
    start_time: float = 0
    filename: str = None
    
    def __init__(self, name, filename):
        self.name = name
        self.filename = f"benchmarks/{filename}"
        create_csv(self.filename, "test,duration_ms")

    def start(self):
        self.start_time = time.perf_counter()
        
    def resume(self):
        """Just an alias for start()"""
        self.start()
        
    def pause(self):
        dur_ms: float = self.get_duration_in_ms()
        self.entries.append(dur_ms)
        self.start_time = 0
        return dur_ms
    
    def add_entry(self, entry: float):
        if entry > 0:
            self.entries.append(entry)

    def end(self):
        """Just an alias for pause()"""
        self.pause()
    
    def to_string(self):
        return f"{self.name},{self.total()}"
    
    def to_csv(self):
        update_csv(self.filename, self.to_string())
    
    def get_duration_in_ms(self) -> float:
        return (time.perf_counter() - self.start_time) * 1000
    
    def total(self) -> float:
        return sum(self.entries)
    
    def reset(self):
        self.entries = []
        self.start_time = 0

def hash256(data: str):
    if type(data) == dict:
        data = stringify(data)
        
    data = data.encode() if type(data) == str else data
    return hashlib.sha256(data).hexdigest()

def stringify(data):
    if type(data) == str:
        return data
    return json.dumps(data, sort_keys=True, separators=(',', ':'))

def parse_json(data):
    if type(data) == str:
        return json.loads(data)
    return data

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
    with open(file, 'a') as f:
        # Write header if file is empty
        if f.tell() == 0 and header:
            f.write(header + '\n')
            
        f.write(line + '\n')
        
def create_csv(file, header, mode = 'a'):
    with open(file, mode) as f:
        if f.tell() == 0:
            f.write(header + '\n')
            
def get_number(prompt, default):
    while True:
        try:
            return int(input(prompt) or default)
        except ValueError:
            print("Invalid input. Please enter a number.")


def wait(seconds):
    for i in range(seconds, 0, -1):
        print(f"\rWaiting {i} seconds...", end='')
        time.sleep(1)
        
def print_human_readable_json(data: dict):
    print(json.dumps(data, indent=2, sort_keys=True))