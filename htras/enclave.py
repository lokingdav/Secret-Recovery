from . import sigma, ec_group

msk, mvk = None, None
retKs = {}

def install():
    global msk, mvk
    if msk is None or mvk is None:
        msk, mvk = sigma.keygen()
    
    
def store(dh_A:str, vk_client: str):
    dh_A: ec_group.Point = ec_group.import_point(dh_A)
    
    dh_b: ec_group.Scalar = ec_group.random_scalar()
    dh_B = ec_group.Point = ec_group.point_from_scalar(dh_b)
    
    retKs[vk_client] = dh_A * dh_b
    dh_B = ec_group.export_point(dh_B)
    
    return (dh_B, vk_client)
    

def verify_ciphertext():
    pass

def remove():
    pass

def recover():
    pass