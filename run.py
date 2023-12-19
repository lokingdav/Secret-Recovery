from htras import simulator
import argparse
    

def init(args):
    simulator.simulate(args.env)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', type=str, help='/path/to/env', required=True)
    args = parser.parse_args()
    
    init(args)