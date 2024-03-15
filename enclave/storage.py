clients: dict = {}

def add_client(vk: str, retK: str):
    global clients
    clients[vk] = retK
    
def get_retK(vk: str):
    return clients[vk]

def remove_client(vk: str):
    global clients
    if vk in clients:
        del clients[vk]
    return True