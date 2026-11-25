from base64 import b64encode, b64decode
from os import rename, makedirs, mkdir
from pathlib import Path
from secrets import token_urlsafe, choice

from nacl.secret import SecretBox
from nacl.utils import random

from .config import REQUEST_INFO, SID_LEN, DATA, SID_POOL, SID_RE
from .exceptions import WriteFailure, ValidationError


def _safe_write(directory: Path, filename: str, content: str):
    temp_file = directory / f'{filename}.tmp'
    main_file = directory / filename
    try:
        with open(temp_file, 'w') as fp:
            fp.write(content)
        rename(temp_file, main_file)
    except OSError as exc:
        raise WriteFailure(msg='writing file failed', status_code=409) from exc


def generate_sid(length: int = SID_LEN, is_request: bool = False) -> str:
    makedirs(DATA, mode=0o700, exist_ok=True)
    makedirs(REQUEST_INFO, mode=0o700, exist_ok=True)
    while True:
        try:
            # Again, mkdir is an atomic operation on POSIX file systems.
            # Two concurrent requests cannot store data into the same
            # directory.
            sid = ''
            for i in range(length):
                sid += choice(SID_POOL)
            mkdir(DATA / sid, mode=0o700)
            if is_request:
                mkdir(REQUEST_INFO / sid, mode=0o700)
            return sid
        except FileExistsError:
            continue


def validate_sid(sid: str | None) -> None:
    if sid is None or not SID_RE.fullmatch(sid):
        raise ValidationError(msg='invalid sid', status_code=400)


def generate_key() -> bytes:
    return random(SecretBox.KEY_SIZE)


def validate_key(key: str | None) -> None:
    # It's random bytes, there's not a lot to validate, except for the
    # length (32 bytes encoded using base64 - minus the rightmost '=').
    if key is None or len(key) != 44 - 1:
        raise ValidationError(msg='invalid key', status_code=400)


def get_key_from_bytes(key_bytes: bytes) -> str:
    # Turn key into base64 and remove padding, because it has the
    # potential of confusing users. ("Is this part of the URL?")
    key = str(b64encode(key_bytes), 'ASCII')
    key = key.replace('/', '_')
    key = key.rstrip('=')
    return key


def get_bytes_from_key(key: str) -> bytes:
    # Restore padding. (No point in using something like a while loop
    # here, we checked for an explicit length earlier.)
    key += '='
    key = key.replace('_', '/')
    return b64decode(key.encode('ASCII'))


def generate_request_token(sid: str) -> str:
    token = token_urlsafe(32)
    _safe_write(directory=REQUEST_INFO / sid, filename='token', content=token)
    return token
