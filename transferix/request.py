from os import mkdir, rename, rmdir
from os.path import isdir, isfile
from pathlib import Path
from re import compile as re_compile

from .crypto import DATA

REQUEST_INFO = Path(DATA) / 'request_infos'
RID_LEN = 8
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


def update_rid_info(rid: str, sid: str, key: str) -> bool:
    lock_dir = REQUEST_INFO / rid / 'lock'
    try:
        mkdir(lock_dir)
    except FileExistsError:
        return False

    temp_file = REQUEST_INFO / rid / 'info.tmp'
    info_file = REQUEST_INFO / rid / 'info'
    try:
        with open(temp_file, 'w') as fp:
            fp.write(f'{sid}|{key}')
        rename(temp_file, info_file)
        return True
    except OSError:
        return False
    finally:
        rmdir(lock_dir)
