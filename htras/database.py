import json
import pathlib
from . import config
import clickhouse_connect
from dotenv import load_dotenv

load_dotenv()

table = "ct_records"

def open_db():
    return clickhouse_connect.get_client(
        host=config.DB_HOST, 
        username=config.DB_USER, 
        password=config.DB_PASS,
        database=config.DB_NAME
    )

def create_table(name, columns, engine='MergeTree()'):
    connection = open_db()
    columns = ', '.join(columns)
    ddl = f"CREATE TABLE IF NOT EXISTS {name} ({columns}) ENGINE = MergeTree()"
    connection.command(ddl)
    
def drop_table(name):
    connection = open_db()
    connection.command(f"DROP TABLE IF EXISTS {name}")
    
def insert(table, records, cols):    
    connection = open_db()
    connection.insert(table, data=records, column_names=cols)
    
def find_all(table, where, limit=None):
    connection = open_db()
    query = f"SELECT idx,cid,hash,data,prev,sig FROM {table} WHERE ({where}) ORDER BY idx DESC"
    query += f" LIMIT {limit}" if limit else ""
    print(query)
    return connection.query(query).result_rows

def find(table, where):
    rows = find_all(table, where, limit=1)
    
    if len(rows) == 0:
        return None
    else:
        return rows[0]
    