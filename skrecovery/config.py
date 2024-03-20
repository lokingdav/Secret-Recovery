from os import getenv
from dotenv import load_dotenv
from collections import namedtuple

load_dotenv(override=True)

def env(envname, default=""):
    value = getenv(envname)
    return value or default

REDIS_DB = env("REDIS_DB")
REDIS_HOST = env("REDIS_HOST")
REDIS_PORT = env("REDIS_PORT")
REDIS_PASS = env("REDIS_PASS")

DB_HOST = env("DB_HOST", "127.0.0.1")
DB_PORT = env("DB_PORT", 27017)
DB_NAME = env("DB_NAME", "skrec")
DB_USER = env("DB_USER", "root")
DB_PASS = env("DB_PASS", "secret")

ENV_FILE = env("ENV_FILE")

# Hyperledger Fabric
NUM_FAULTS = int(env("NUM_FAULTS", 2))
NUM_PEERS = int(env("NUM_PEERS", 25))
NUM_ORDERERS = int(env("NUM_ORDERERS", 7))
NUM_ENDORSEMENTS = int(env("NUM_ENDORSEMENTS", 15))
MAX_TXS_PER_BLOCK = int(env("MAX_TXS_PER_BLOCK", 10))

T_OPEN_BUFFER = int(env("T_OPEN_BUFFER", 1))

ORDER_SERVICE_CONFIG = {
    "NUM_FAULTS": NUM_FAULTS,
    "NUM_PEERS": NUM_PEERS,
    "NUM_ORDERERS": NUM_ORDERERS,
    "NUM_ENDORSEMENTS": NUM_ENDORSEMENTS,
    "MAX_TXS_PER_BLOCK": MAX_TXS_PER_BLOCK
}