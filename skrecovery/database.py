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
        txs = list(collection.find(sort=[('created_at', -1)], limit=config.MAX_TXS_PER_BLOCK))
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