from htras import commitment

def test_commitment():
    message = "Hello World!"
    com, secret = commitment.commit(message)
    
    com_hex = commitment.export_com(com)
    imported_com = commitment.import_com(com_hex)
    assert com == imported_com
    
    secret_hex = commitment.export_secret(secret)
    imported_secret = commitment.import_secret(secret_hex)
    assert secret == imported_secret
    
    print(f"Commitment: {com_hex}")
    print(f"Secret: {secret_hex}")
    
    assert commitment.open_com(com, message, secret)
    
    print("Commitment scheme works!")
    

test_commitment()