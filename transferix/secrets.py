from flask import request, url_for

from transferix.crypto import store, generate_key, generate_sid, get_key_from_bytes, get_bytes_from_key, \
    ValidationError, validate_sid, REQUEST_INFO
from transferix.errorhandler import TransferixException
from transferix.request import validate_request, update_request_status, RequestStatus


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
        is_request = True
        key_bytes = get_bytes_from_key(key)
        validate_request(sid=sid)
    elif sid is None and key is None:
        is_request = False
        key_bytes = generate_key()
        key = get_key_from_bytes(key_bytes)
        sid = generate_sid()
    else:
        raise TransferixException(msg='invalid parameters', status_code=400)

    store(sid=sid, secret_bytes=secret_bytes, key_bytes=key_bytes, filename=filename)
    if is_request:
        update_request_status(sid=sid, status=RequestStatus.STORED)
    return url_for('get', sid=sid, key=key, _external=True)


def validate_reveal(sid: str, token: str | None = None) -> bool:
    validate_sid(sid)
    if (REQUEST_INFO / sid / 'token').is_file():
        try:
            with open(REQUEST_INFO / sid / 'token', 'r') as fp:
                request_token = fp.read()
        except Exception as e:
            raise ValidationError(msg='invalid secret token', status_code=400) from e
        if token is None or request_token != token:
            raise ValidationError(msg='invalid secret token', status_code=400)
        return True
    else:
        return False


def secret_ready(sid: str, token: str) -> bool:
    validate_request(sid=sid)
    validate_reveal(sid=sid, token=token)

    with open(REQUEST_INFO / sid / 'status') as fp:
        status = fp.read()

    if status == RequestStatus.STORED:
        return True

    return False
