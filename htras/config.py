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

LEDGER_MINERS = 'ledger:miners'
LEDGER_MINERS_COUNT = 'ledger:miners:count'
LEDGER_BLOCKS = 'ledger:blocks'