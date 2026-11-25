from os import rename
from shutil import rmtree
from subprocess import run

from nacl.secret import SecretBox

from .config import DATA, REQUEST_INFO, SHRED_CMD
from .exceptions import TransferixException, ValidationError
from .keys import get_bytes_from_key


def retrieve(sid: str, key: str) -> tuple[bytes | None, str | None]:
    # Try to rename this sid's directory. This is an atomic operation on
    # POSIX file systems, meaning two concurrent requests cannot rename
    # the same directory -- for one of them, it will look like the
    # source directory does not exist. This also implicitly covers the
    # case where we try to retrieve an invalid sid.
    locked_sid = sid + '_locked'
    try:
        rename(DATA / sid, DATA / locked_sid)
    except OSError as exc:
        raise TransferixException(msg='already revealed', status_code=410) from exc

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

    # Destroy the secret *now*, before trying to decrypt it.
    #
    # a) The logic required to attempt decryption and then *unlock* the
    #    secret again when that fails is more complicated.
    # b) If we decrypt a secret and then deletion fails for whatever
    #    absurd reason, then we risk allowing to decrypt/reveal the same
    #    secret twice.
    #
    # The easiest thing to *reason about* is to destroy a secret as
    # early as possible.
    #
    # It's fine if that means that users might need to retransmit a
    # secret in corner cases or attack scenarios.
    rmtree(DATA / locked_sid)
    rmtree(REQUEST_INFO / sid, ignore_errors=True)

    try:
        box = SecretBox(get_bytes_from_key(key))
        decrypted_bytes = box.decrypt(secret_bytes)
    except Exception as exc:
        raise TransferixException(msg='wrong key', status_code=400) from exc
    return decrypted_bytes, filename


def secret_exists_as_file(sid: str) -> bool:
    if not (DATA / sid).is_dir():
        raise TransferixException(msg='already revealed', status_code=410)
    return (DATA / sid / 'filename').is_file()


def store(sid: str, secret_bytes: bytes, key_bytes: bytes, filename: str | None):
    if filename is not None and not filename.isprintable():
        raise ValidationError(msg='filename not printable', status_code=400)

    box = SecretBox(key_bytes)
    try:
        with open(DATA / sid / 'secret', 'xb') as fp:
            fp.write(box.encrypt(secret_bytes))
    except FileExistsError as exc:
        raise TransferixException(msg='already stored', status_code=409) from exc

    if filename is not None:
        with open(DATA / sid / 'filename', 'w') as fp:
            fp.write(filename)
