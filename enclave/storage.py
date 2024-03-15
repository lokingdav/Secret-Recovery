clients: dict = {}

def add_client(vk: str, retK: str):
    global clients
    clients[vk] = retK
    
def get_retK(vk: str):
    return clients[vk]