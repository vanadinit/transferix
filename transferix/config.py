from os import getenv
from pathlib import Path
from re import compile as re_compile
from shutil import which
from string import ascii_letters, digits

DATA = Path(getenv('TRANSFERIX_DATA', '/tmp'))
REQUEST_INFO = DATA / 'request_infos'
MAX_FILE_SIZE = int(getenv('TRANSFERIX_MAX_FILE_SIZE', 10_000_000))

SID_LEN = 8
SID_RE = re_compile(f'^[A-Za-z0-9]{{{SID_LEN}}}$')
SID_POOL = ascii_letters + digits

SHRED_CMD = str(which('shred'))
if 'shred' not in SHRED_CMD:
    raise Exception('shred command not found')
