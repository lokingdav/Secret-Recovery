import socket, hashlib, json
import vsock
from enclave.response import EnclaveRes
from skrecovery.helpers import parse_json

SERVER = (socket.gethostbyname(socket.gethostname()), 5005) # SET to None if running locally

if __name__ == "__main__":
    connection: socket.socket = vsock.connect(address=SERVER)
    msg: str = json.dumps({"msg": "Hello World!"})
    print(f"Sending: {msg}")
    vsock.send(connection, msg=msg)
    res: str = vsock.response_recv(connection)
    res: EnclaveRes = EnclaveRes.deserialize(parse_json(res))
    print(f"Received: {res.serialize()}")
    vsock.disconnect(connection)