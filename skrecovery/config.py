from os import getenv
from dotenv import load_dotenv
from collections import namedtuple

load_dotenv()

def env(envname, default=""):
    value = getenv(envname)
    return value or default

REDIS_DB = env("REDIS_DB")
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_PASS = env("REDIS_PASS")

DB_HOST = env("DB_HOST", "127.0.0.1")
DB_NAME = env("DB_NAME", "skrec")
DB_USER = env("DB_USER", "root")
DB_PASS = env("DB_PASS", "secret")

ENV_FILE = env("ENV_FILE")

# Hyperledger Fabric
NUM_PEERS = int(env("NUM_PEERS", 25))
NUM_ORDERERS = int(env("NUM_ORDERERS", 7))
NUM_ENDORSEMENTS = int(env("NUM_ENDORSEMENTS", 15))
