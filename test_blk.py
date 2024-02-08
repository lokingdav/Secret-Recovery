from htras import chain

chain.init()
blk = chain.create_block('0')
# print(blk['hash'], blk['prev_hash'], len(blk['sigs']))
# print(chain.validate_block(blk))

window = chain.create_window(10)
print(chain.validate_window(window))