from htras import enc_dec_scheme, sigma, ec_group, helpers, enclave, chain

enclave.install()

num_runs = 1
secret = helpers.random_bytes(32) # Client's secret
perm_info = helpers.random_bytes(32) # Client perm information

header = 'test_name,index,runtime_ms'
helpers.create_csv('bench-secrec.csv', header, mode='w')

def write_to_benchsecrec(testname, index, runtime):
    helpers.update_csv('bench-secrec.csv', f'{testname},{index},{runtime}')

def bench_store():
    for i in range(num_runs):
        # client part 1
        client_p1_start = helpers.startStopwatch()
        csk, cvk = sigma.keygen()
        a, A = ec_group.random_DH()
        client_p1_time = helpers.stopStopwatch(client_p1_start)
        
        # cloud part 1
        cloud_p1_start = helpers.startStopwatch()
        B, vkclient, sig = enclave.store(A, cvk)
        cloud_p1_time = helpers.stopStopwatch(cloud_p1_start)
        
        # client part 2
        client_p2_start = helpers.startStopwatch()
        esmsg = f"{vkclient}|{A.hex()}|{B.hex()}"
        sigma.verify(enclave.getpk(), esmsg, sig)
        retK = a * B
        aes_data = perm_info + b'|' + secret
        aes_ctx = enc_dec_scheme.aes_enc(retK, aes_data)
        client_p2_time = helpers.stopStopwatch(client_p2_start)
        
        # cloud part 2
        cloud_p2_start = helpers.startStopwatch()
        enclave.verify_ciphertext(vkclient, perm_info, aes_ctx)
        cloud_p2_time = helpers.stopStopwatch(cloud_p2_start)
    
        write_to_benchsecrec('client-store', i, client_p1_time + client_p2_time)
        write_to_benchsecrec('cloud-store', i, cloud_p1_time + cloud_p2_time)
    
def bench_remove():
    csk, cvk = sigma.keygen()
    remove_msg = b"remove" + b"|" + perm_info
    
    for i in range(num_runs):
        # client part 1
        client_p1_start = helpers.startStopwatch()
        remove_sig = sigma.sign(csk, remove_msg)
        client_p1_time = helpers.stopStopwatch(client_p1_start)
        
        # cloud part 1
        cloud_p1_start = helpers.startStopwatch()
        if not sigma.verify(cvk, remove_msg, remove_sig):
            raise Exception("Cloud: remove_sig failed verification")
        sig_att = enclave.remove(cvk, perm_info, remove_sig)
        cloud_p1_time = helpers.stopStopwatch(cloud_p1_start)
        
        # client part 2
        client_p2_start = helpers.startStopwatch()
        msg = b"removed" + b'|' + perm_info + b'|' + bytes(remove_sig)
        if not sigma.verify(enclave.getpk(), msg, sig_att):
            raise Exception("Client: sig_att failed verification")
        client_p2_time = helpers.stopStopwatch(client_p2_start)
        
        write_to_benchsecrec('client-remove', i, client_p1_time + client_p2_time)
        write_to_benchsecrec('cloud-remove', i, cloud_p1_time)

def bench_retrieved():
    csk, cvk = sigma.keygen()
    ret_payl = b"retrieve" + b'|' + perm_info
    cretK = ec_group.point_from_scalar(ec_group.random_scalar())
    
    for i in range(num_runs):
        # client part 1
        client_p1_start = helpers.startStopwatch()
        sig_ret = sigma.sign(csk, ret_payl)
        client_p1_time = helpers.stopStopwatch(client_p1_start)
        
        # cloud part 1
        cloud_p1_start = helpers.startStopwatch()
        if not sigma.verify(cvk, ret_payl, sig_ret):
            raise Exception("Cloud: sig_ret failed verification")
        cloud_p1_time = helpers.stopStopwatch(cloud_p1_start)

        plaintext = perm_info + b'|' + secret
        aes_ctx = enc_dec_scheme.aes_enc(cretK, plaintext)
        
        # client part 2
        client_p2_start = helpers.startStopwatch()
        plaintext_prime = enc_dec_scheme.aes_dec(cretK, aes_ctx)
        client_p2_time = helpers.stopStopwatch(client_p2_start)
        assert plaintext == plaintext_prime
        
        write_to_benchsecrec('client-retrieved', i, client_p1_time + client_p2_time)
        write_to_benchsecrec('cloud-retrieved', i, cloud_p1_time)

def bench_recover():
    # setup for recover
    original_secret = perm_info + b'|' + secret
    csk, cvk = sigma.keygen()
    ssk, svk = sigma.keygen()
    lsk, lvk = sigma.keygen()
    ssig = sigma.sign(ssk, b"recover")
    lsig = sigma.sign(lsk, b"recover")
    cretK = ec_group.point_from_scalar(ec_group.random_scalar())
    aes_ctx = enc_dec_scheme.aes_enc(cretK, original_secret)
    enclave.set_client_retK(cvk, cretK)
    chain.init()
    
    for i in range(num_runs):
        
        # client part 1
        client_p1_start = helpers.startStopwatch()
        pubk, privk = enc_dec_scheme.rsa_keygen()
        req = b"recover" + b'|' + pubk.export_key()
        
        client_p1_time = helpers.stopStopwatch(client_p1_start)
        
        # cloud part 1
        cloud_p1_start = helpers.startStopwatch()
        
        permission = {
            'chal_window_c': chain.create_window(10),
            'chal_window_req': chain.create_window(10),
            'com_window': chain.create_window(10),
            'txs': {
                'data': 'test'
            },
        }
        
        enclave.begin_recovery(data={
            'pubk': pubk,
            'aes_ctx' : aes_ctx,
            'req': req,
            'perm': permission,
        })
        
        # verify chal_window_c one at a time
        for j in range(0, len(permission['chal_window_c'])):
            enclave.verify_chal_window_c(permission['chal_window_c'][j])
            
        # verify chal_window_req one at a time
        for j in range(0, len(permission['chal_window_req'])):
            enclave.verify_chal_window_req(permission['chal_window_req'][j])
            
        # verify com_window_s one at a time
        for j in range(0, len(permission['com_window'])):
            enclave.verify_com_window(permission['com_window'][j])
        
        print(enclave.previous_hashes)
        print(enclave.valid_windows)
        return 
        rsa_ctx, sig_att = enclave.end_recovery()
        
        cloud_p1_time = helpers.stopStopwatch(cloud_p1_start)
        
        # client part 2
        client_p2_start = helpers.startStopwatch()
        assert sigma.verify(enclave.getpk(), enc_dec_scheme.rsa_ctx_to_bytes(rsa_ctx) + b'|' + perm_info, sig_att)
        mysecret = enc_dec_scheme.rsa_dec(privk, rsa_ctx)
        client_p2_time = helpers.stopStopwatch(client_p2_start)
        
        write_to_benchsecrec('client-recover', i, client_p1_time + client_p2_time)
        write_to_benchsecrec('cloud-recover', i, cloud_p1_time)
        
if __name__ == '__main__':
    bench_recover()