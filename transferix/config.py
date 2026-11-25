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


def _human_format_size(size: int) -> str:
    for div, suff in (
            (1_000_000_000, 'GB'),
            (1_000_000, 'MB'),
            (1_000, 'kB'),
    ):
        if size >= div:
            return f'{size // div} {suff}'
    return f'{size} Bytes'


MAX_FILE_SIZE_HUMAN = _human_format_size(MAX_FILE_SIZE)
