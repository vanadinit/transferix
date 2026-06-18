from base64 import b64decode, b64encode
from os import environ, mkdir, rename
from os.path import isdir, isfile, join
from random import choice
from re import compile as re_compile
from shutil import rmtree
from string import ascii_letters, digits
from subprocess import run

from nacl.secret import SecretBox
from nacl.utils import random

DATA = environ.get('TRANSFERIX_DATA', '/tmp')
SID_LEN = 4
SID_VALIDATOR = re_compile(f'^[A-Za-z0-9]{{{SID_LEN}}}$')

ALREADY_REVEALED = 0
WRONG_KEY = 1
OK = 2


def generate_sid(length: int = SID_LEN) -> str:
    pool = ascii_letters + digits
    sid = ''
    for i in range(length):
        sid += choice(pool)
    return sid


def retrieve(sid: str, key: str) -> tuple[bytes | None, str | None, int]:
    # Try to rename this sid's directory. This is an atomic operation on
    # POSIX file systems, meaning two concurrent requests cannot rename
    # the same directory -- for one of them, it will look like the
    # source directory does not exist. This also implicitly covers the
    # case where we try to retrieve an invalid sid.
    locked_sid = sid + '_locked'
    try:
        rename(join(DATA, sid), join(DATA, locked_sid))
    except OSError:
        return None, None, ALREADY_REVEALED

    # Now that we have "locked" this sid, we can safely read it and then
    # destroy it.
    with open(join(DATA, locked_sid, 'secret'), 'rb') as fp:
        secret_bytes = fp.read()
    run(['/usr/bin/shred', join(DATA, locked_sid, 'secret')])

    try:
        with open(join(DATA, locked_sid, 'filename'), 'r') as fp:
            filename = fp.read()
        run(['/usr/bin/shred', join(DATA, locked_sid, 'filename')])
    except FileNotFoundError:
        filename = None

    rmtree(join(DATA, locked_sid))

    # Restore padding. (No point in using something like a while loop
    # here, we checked for an explicit length earlier.)
    key += '='
    key = key.replace('_', '/')
    key_bytes = b64decode(key.encode('ASCII'))
    try:
        box = SecretBox(key_bytes)
        decrypted_bytes = box.decrypt(secret_bytes)
    except Exception:
        return None, None, WRONG_KEY
    return decrypted_bytes, filename, OK


def secret_exists(sid: str) -> tuple[bool, bool]:
    return isdir(join(DATA, sid)), isfile(join(DATA, sid, 'filename'))


def store(secret_bytes: bytes, filename: str | None) -> tuple[str, str]:
    while True:
        try:
            # Again, mkdir is an atomic operation on POSIX file systems.
            # Two concurrent requests cannot store data into the same
            # directory.
            sid = generate_sid()
            mkdir(join(DATA, sid))
            break
        except FileExistsError:
            continue

    key_bytes = random(SecretBox.KEY_SIZE)
    box = SecretBox(key_bytes)

    with open(join(DATA, sid, 'secret'), 'wb') as fp:
        fp.write(box.encrypt(secret_bytes))

    if filename is not None:
        with open(join(DATA, sid, 'filename'), 'w') as fp:
            fp.write(filename)

    # Turn key into base64 and remove padding, because it has the
    # potential of confusing users. ("Is this part of the URL?")
    key = str(b64encode(key_bytes), 'ASCII')
    key = key.replace('/', '_')
    key = key.rstrip('=')

    return sid, key


def validate_key(key: str) -> None:
    # It's random bytes, there's not a lot to validate, except for the
    # length (32 bytes encoded using base64 - minus the rightmost '=').
    assert len(key) == 44 - 1


def validate_sid(sid: str) -> None:
    assert SID_VALIDATOR.search(sid) is not None
