from base64 import b64decode, b64encode
from os import environ, mkdir, rename, makedirs
from pathlib import Path
from re import compile as re_compile
from secrets import choice
from shutil import rmtree, which
from string import ascii_letters, digits
from subprocess import run

from nacl.secret import SecretBox
from nacl.utils import random

from transferix.errorhandler import TransferixException

DATA = Path(environ.get('TRANSFERIX_DATA', '/tmp'))
REQUEST_INFO = DATA / 'request_infos'

SID_LEN = 8
SID_RE = re_compile(f'^[A-Za-z0-9]{{{SID_LEN}}}$')
SID_POOL = ascii_letters + digits

ALREADY_REVEALED = 0
WRONG_KEY = 1
OK = 2

SHRED_CMD = str(which('shred'))
if 'shred' not in SHRED_CMD:
    raise Exception('shred command not found')


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


def retrieve(sid: str, key: str) -> tuple[bytes | None, str | None, int]:
    # Try to rename this sid's directory. This is an atomic operation on
    # POSIX file systems, meaning two concurrent requests cannot rename
    # the same directory -- for one of them, it will look like the
    # source directory does not exist. This also implicitly covers the
    # case where we try to retrieve an invalid sid.
    locked_sid = sid + '_locked'
    try:
        rename(DATA / sid, DATA / locked_sid)
    except OSError:
        return None, None, ALREADY_REVEALED

    # Now that we have "locked" this sid, we can safely read it and then
    # destroy it.
    with open(DATA / locked_sid / 'secret', 'rb') as fp:
        secret_bytes = fp.read()
    run([SHRED_CMD, DATA / locked_sid / 'secret'])

    try:
        with open(DATA / locked_sid / 'filename', 'r') as fp:
            filename = fp.read()
        run([SHRED_CMD, DATA / locked_sid / 'filename'])
    except FileNotFoundError:
        filename = None

    rmtree(DATA / locked_sid)

    try:
        box = SecretBox(get_bytes_from_key(key))
        decrypted_bytes = box.decrypt(secret_bytes)
    except Exception:
        return None, None, WRONG_KEY
    return decrypted_bytes, filename, OK


def secret_exists_as_file(sid: str) -> bool:
    if not (DATA / sid).is_dir():
        raise TransferixException(msg='already revealed', status_code=410)
    return (DATA / sid / 'filename').is_file()


def generate_key() -> bytes:
    return random(SecretBox.KEY_SIZE)


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


def store(sid: str, secret_bytes: bytes, key_bytes: bytes, filename: str | None):
    if filename is not None and not filename.isprintable():
        raise ValidationError(msg='Non-printable characters in filename', status_code=400)

    box = SecretBox(key_bytes)
    try:
        with open(DATA / sid / 'secret', 'xb') as fp:
            fp.write(box.encrypt(secret_bytes))
    except FileExistsError as exc:
        raise TransferixException(msg='secret already stored', status_code=409) from exc

    if filename is not None:
        with open(DATA / sid / 'filename', 'w') as fp:
            fp.write(filename)


def validate_key(key: str | None) -> None:
    # It's random bytes, there's not a lot to validate, except for the
    # length (32 bytes encoded using base64 - minus the rightmost '=').
    if key is None or len(key) != 44 - 1:
        raise ValidationError(msg='Key validation failed', status_code=400)


def validate_sid(sid: str | None) -> None:
    if sid is None or not SID_RE.fullmatch(sid):
        raise ValidationError(msg='SID validation failed', status_code=400)


class ValidationError(TransferixException):
    pass
