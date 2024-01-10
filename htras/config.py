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

DB_HOST = env("DB_HOST")
DB_NAME = env("DB_NAME")
DB_USER = env("DB_USER")
DB_PASS = env("DB_PASS")

ENV_FILE = env("ENV_FILE")