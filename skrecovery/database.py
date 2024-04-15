from . import config
import json, pathlib
from pymongo import MongoClient

def open_db():
    uri = f"mongodb://{config.DB_USER}:{config.DB_PASS}@{config.DB_HOST}:{config.DB_PORT}/"
    return MongoClient(uri)
                
def insert(table, records):
    results = None
    
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db[table]
        results = collection.insert_many(records)
        
    return results.inserted_ids

def save_fabric_keys(data: dict):
    existing: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['fabric_keys']
        existing = collection.find_one()
        if existing:
            collection.update_one({'_id': existing['_id']}, {'$set': data})
        else:
            collection.insert_one(data)

def load_fabric_keys():
    keys: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['fabric_keys']
        keys = collection.find_one()
    return keys

def insert_pending_txs(records):
    return insert('pending_txs', records)
    
def get_latest_block():
    block: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        block = collection.find_one(sort=[('_id', -1)])
    return block

def delete_blocks_after(number: int):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        collection.delete_many({'_id': {'$gt': number}})

def find_block_by_number(number: int):
    block: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        block = collection.find_one({'_id': number})
    return block

def get_pending_txs():
    txs: list[dict] = []
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['pending_txs']
        txs = list(collection.find(sort=[('created_at', 1)], limit=config.MAX_TXS_PER_BLOCK))
    return txs

def delete_pending_txs(txs: list[dict]):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['pending_txs']
        ids = [tx['_id'] for tx in txs]
        collection.delete_many({'_id': {'$in': ids}})
        
def save_block(data: dict):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        block = collection.find_one({'_id': data['_id']})
        if not block:
            collection.insert_one(data)
            
def get_chain():
    chain: list[dict] = []
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        chain = list(collection.find(sort=[('_id', 1)]))
    return chain

def find_block_by_transaction_id(tx_id: str):
    block: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        block = collection.find_one({'data._id': tx_id})
    return block

def find_user_by_id(user_id: str):
    user: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['users']
        user = collection.find_one({'_id': user_id})
    return user

def insert_user(data: dict):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['users']
        collection.insert_one(data)
        
def get_server_customer(server_id: str, perm_hash: str):
    customer: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['server_customers']
        customer = collection.find_one({'server_id': server_id, 'perm_hash': perm_hash})
    return customer

def insert_server_customer(server_id: str, perm_hash: str):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['server_customers']
        collection.insert_one({'server_id': server_id, 'perm_hash': perm_hash})
        
def remove_server_customer(server_id: str, perm_hash: str):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['server_customers']
        collection.delete_one({'server_id': server_id, 'perm_hash': perm_hash})
        
        
def insert_ctx(server_id: str, perm_hash: str, ctx: str):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ciphertexts']
        # find if ctx already exists
        existing = collection.find_one({
            '_id': perm_hash, 
            'server_id': server_id
        })
        if existing:
            collection.update_one({'_id': perm_hash}, {'$set': {'ctx': ctx}})
        else:
            collection.insert_one({
                '_id': perm_hash,
                'server_id': server_id,
                'ctx': ctx
            })
def retrieve_ctx(server_id: str, perm_hash: str):
    data: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ciphertexts']
        data = collection.find_one({'_id': perm_hash, 'server_id': server_id})
    return data

def remove_ctx(server_id: str, perm_hash: str):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ciphertexts']
        collection.delete_one({'_id': perm_hash, 'server_id': server_id})
            
def update_user(user: dict):
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['users']
        collection.update_one({'_id': user['_id']}, {'$set': user})
        
def find_blocks_in_range(start_number: int, end_number: int):
    blocks: list[dict] = []
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        blocks = list(collection.find({'_id': {'$gte': start_number, '$lte': end_number}}))
    return blocks

def find_block_by_filters(filters: dict):
    block: dict = None
    with open_db() as connection:
        db = connection[config.DB_NAME]
        collection = db['ledgers']
        block = collection.find_one(filters)
    return block

def insert_wait_window(blocks: list[dict]):
    return insert('wait_window', blocks)