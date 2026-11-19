from os.path import isfile, isdir
from shutil import rmtree

from flask import request, url_for

from transferix.crypto import store
from transferix.errorhandler import TransferixException
from transferix.request import is_valid_unused_rid, update_rid_info, REQUEST_INFO, is_valid_rid


def new_secret(rid: str | None, data: str | None) -> str:
    if rid and not is_valid_unused_rid(rid):
        raise TransferixException(msg='rid missing or invalid', status_code=400)

    if data:
        secret_bytes = data.encode('UTF-8')
        filename = None
    else:
        secret_bytes = request.files['file'].read()
        filename = request.files['file'].filename

    if filename is None and len(secret_bytes.strip()) <= 0:
        raise TransferixException(msg='empty secret', status_code=400)

    sid, key = store(secret_bytes, filename)
    if rid and not update_rid_info(rid=rid, sid=sid, key=key):
        raise TransferixException(msg='rid missing or invalid', status_code=400)

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