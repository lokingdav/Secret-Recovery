import argparse
from skrecovery.vsock import VsockServer

def start_enclave(port: int):
    try:
        server: VsockServer = VsockServer()
        server.bind(port)
        server.listen()
    except Exception as e:
        print(f"Failed to start enclave: {e}")
        exit(1)

def main():
    parser = argparse.ArgumentParser(prog='vsock-sample')
    parser.add_argument('-p', '--port', type=int, help='The local port to listen on.')
    args = parser.parse_args()
    port = args.port if args.port else 5005
    start_enclave(port)

if __name__ == "__main__":
    main()
