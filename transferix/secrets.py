from os.path import isfile, isdir
from shutil import rmtree

from flask import request, url_for

from transferix.crypto import store, generate_key, generate_sid, get_key_from_bytes, get_bytes_from_key
from transferix.errorhandler import TransferixException
from transferix.request import REQUEST_INFO, is_valid_rid


def new_secret(data: str | None, sid: str | None, key: str | None) -> str:
    filename = None
    secret_bytes = b''
    if data:
        secret_bytes = data.encode('UTF-8')
    elif request.files.get('file'):
        secret_bytes = request.files['file'].read()
        filename = request.files['file'].filename

    if filename is None and len(secret_bytes.strip()) <= 0:
        raise TransferixException(msg='empty secret', status_code=400)

    if sid and key:
        key_bytes = get_bytes_from_key(key)
        # TODO validate_request(sid, key)
    elif sid is None and key is None:
        key_bytes = generate_key()
        key = get_key_from_bytes(key_bytes)
        sid = generate_sid()
    else:
        raise TransferixException(msg='invalid parameters', status_code=400)

    store(sid=sid, secret_bytes=secret_bytes, key_bytes=key_bytes, filename=filename)
    return url_for('get', sid=sid, key=key, _external=True)


def consume_secret(rid: str) -> tuple[str, str]:
    if not is_valid_rid(rid) or not isdir(REQUEST_INFO / rid):
        raise TransferixException(msg='rid missing or invalid', status_code=400)

    if isfile(REQUEST_INFO / rid / 'info'):
        with open(REQUEST_INFO / rid / 'info') as fp:
            sid, key = fp.read().split('|')
        rmtree(REQUEST_INFO / rid)
        return sid, key

    raise NotReadyYetException()


class NotReadyYetException(Exception):
    pass
