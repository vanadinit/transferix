from flask import request, url_for
from markupsafe import escape

from .config import REQUEST_INFO, DATA
from .crypto import store
from .exceptions import RequestStateException, TransferixException, ValidationError
from .keys import generate_sid, generate_key, get_key_from_bytes, get_bytes_from_key, validate_key, validate_sid


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
        validate_request(sid=sid, status='init')
        validate_key(key)
        key_bytes = get_bytes_from_key(key)
    elif sid is None and key is None:
        key_bytes = generate_key()
        key = get_key_from_bytes(key_bytes)
        sid = generate_sid()
    else:
        raise TransferixException(msg='invalid parameters', status_code=400)

    store(sid=sid, secret_bytes=secret_bytes, key_bytes=key_bytes, filename=filename)
    return url_for('get', sid=sid, key=key, _external=True)


def validate_reveal(sid: str | None, token: str | None = None):
    validate_sid(sid)
    if (REQUEST_INFO / sid / 'token').is_file():
        try:
            with open(REQUEST_INFO / sid / 'token', 'r') as fp:
                request_token = fp.read()
        except Exception as exc:
            raise ValidationError(msg='invalid secret token', status_code=400) from exc
        if token is None or request_token != token:
            raise ValidationError(msg='invalid secret token', status_code=400)
        if not (DATA / sid / 'secret').is_file():
            raise RequestStateException(msg='no secret stored', status_code=400)


def get_request_strs(sid: str | None, key: str | None, target: str) -> tuple[str, str]:
    if sid and key:
        validate_request(sid=sid, status='init')
        request_path = url_for(target, sid=sid, key=key)
        request_fields = (f'<input name="sid" type="hidden" value="{escape(sid)}">'
                          f'<input name="key" type="hidden" value="{escape(key)}">')
    else:
        request_path = url_for(target)
        request_fields = ''

    return request_path, request_fields


def validate_request(sid: str | None, status: str):
    if sid is None:
        raise ValidationError(msg='sid missing', status_code=400)
    validate_sid(sid)
    if not (REQUEST_INFO / sid).is_dir():
        raise ValidationError(msg='invalid secret ID', status_code=400)

    match status:
        case 'init':
            if not (REQUEST_INFO / sid / 'token').is_file():
                raise RequestStateException(msg='request is in wrong state', status_code=409)
        case 'stored':
            if not (DATA / sid / 'secret').is_file():
                raise RequestStateException(msg='request is in wrong state', status_code=409)
        case _:
            raise TransferixException(msg='Programming error. Please notify developers.', status_code=500)


def secret_ready(sid: str | None, token: str | None) -> bool:
    try:
        validate_request(sid=sid, status='stored')
    except RequestStateException:
        return False
    validate_reveal(sid=sid, token=token)
    return True
