import json
import pathlib
from . import config
import mysql.connector as mysql

table = "ct_records"

def open_db():
    return mysql.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        passwd=config.DB_PASS,
        database=config.DB_NAME
    )

def create_table(name, columns, engine='InnoDB'):
    with open_db() as connection:
        columns = ', '.join(columns)
        ddl = f"CREATE TABLE IF NOT EXISTS {name} ({columns}) ENGINE = {engine}"
        with connection.cursor() as cursor:
            cursor.execute(ddl)
    
def drop_table(names):
    with open_db() as connection:
        with connection.cursor() as cursor:
            for name in names:
                cursor.execute(f"DROP TABLE IF EXISTS {name}")
                
                
def insert(table, records, cols):    
    with open_db() as connection:
        with connection.cursor() as cursor:
            placeholders = ', '.join(['%s'] * len(cols))
            cols = ', '.join(cols)
            query = f"INSERT INTO {table} ({cols}) VALUES ({placeholders})"
            # print(query)
            cursor.executemany(query, records)
        connection.commit()
    
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

def find(table, where):
    rows = find_all(table, where, limit=1)
    return None if len(rows) == 0 else rows[0]