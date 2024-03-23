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
    parser.add_argument('-p', '--port', type=int, help='The local port to listen on.', default=5005)
    args = parser.parse_args()
    start_enclave(args.port)

if __name__ == "__main__":
    main()
