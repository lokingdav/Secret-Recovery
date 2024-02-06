from htras import aes, sigma, ec_group, helpers, enclave

enclave.install()

num_runs = 100
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
        nonce, ctx, mac = aes.enc(retK, aes_data)
        client_p2_time = helpers.stopStopwatch(client_p2_start)
        
        # cloud part 2
        cloud_p2_start = helpers.startStopwatch()
        enclave.verify_ciphertext(vkclient, perm_info, (nonce, ctx, mac))
        cloud_p2_time = helpers.stopStopwatch(cloud_p2_start)
    
        write_to_benchsecrec('client-store', i, client_p1_time + client_p2_time)
        write_to_benchsecrec('cloud-store', i, cloud_p1_time + cloud_p2_time)
    
    
if __name__ == '__main__':
    bench_store()