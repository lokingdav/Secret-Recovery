from Crypto.Cipher import AES

def enc(key, data):
    cipher = AES.new(key, AES.MODE_EAX)
    nonce = cipher.nonce
    ctx, mac = cipher.encrypt_and_digest(data)
    return (nonce, ctx, mac)

def dec(key, nonce, ctx, mac):
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    plaintext = cipher.decrypt(ctx)
    cipher.verify(mac)
    
    return plaintext