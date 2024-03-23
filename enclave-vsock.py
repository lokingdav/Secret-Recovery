import argparse
from skrecovery.vsock import VsockServer

def start_enclave(port: int):
    server: VsockServer = VsockServer()
    server.bind(port)
    server.listen()

def main():
    parser = argparse.ArgumentParser(prog='vsock-sample')
    parser.add_argument('-p', '--port', type=int, help='The local port to listen on.')
    args = parser.parse_args()
    
    start_enclave(args.port)

if __name__ == "__main__":
    main()
