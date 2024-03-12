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
    
def find_all(table, cols=None, where=None, order=None, limit=None):
    items = []
    with open_db() as connection:
        cols = ', '.join(cols) if cols else '*'
        with connection.cursor(dictionary=True) as cursor:
            query = f"SELECT {cols} FROM {table}"
            query += f" WHERE {where}" if where else ""
            query += f" ORDER BY {order}" if order else ""
            query += f" LIMIT {limit}" if limit else ""
            cursor.execute(query)
            items = cursor.fetchall()
    return items

def find(table, where=None, order=None):
    rows = find_all(table, where=where, order=order, limit=1)
    return None if len(rows) == 0 else rows[0]