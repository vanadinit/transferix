from os import mkdir, rename, makedirs
from os.path import isdir, isfile
from pathlib import Path
from re import compile as re_compile

from .crypto import DATA, generate_sid

REQUEST_INFO = Path(DATA) / 'request_infos'
RID_LEN = 27
RID_VALIDATOR = re_compile(f'^[A-Za-z0-9]{{{RID_LEN}}}$')


def is_valid_rid(rid: str | None) -> bool:
    return bool(rid and isinstance(rid, str) and RID_VALIDATOR.search(rid))


def is_valid_unused_rid(rid: str | None) -> bool:
    if not is_valid_rid(rid):
        return False
    if not isdir(REQUEST_INFO / rid):
        return False
    if isfile(REQUEST_INFO / rid / 'info'):
        return False
    return True


def create_rid() -> str:
    makedirs(REQUEST_INFO, exist_ok=True)
    while True:
        try:
            rid = generate_sid(length=RID_LEN)
            mkdir(REQUEST_INFO / rid)
            return rid
        except FileExistsError:
            continue


def update_rid_info(rid: str, sid_url: str) -> bool:
    lock_dir = REQUEST_INFO / rid / 'lock'
    try:
        mkdir(lock_dir)
    except FileExistsError:
        return False

    temp_file = REQUEST_INFO / rid / 'info.tmp'
    info_file = REQUEST_INFO / rid / 'info'
    try:
        with open(temp_file, 'w') as fp:
            fp.write(sid_url)
        rename(temp_file, info_file)
        return True
    except OSError:
        return False
