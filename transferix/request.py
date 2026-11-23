from os import rename
from pathlib import Path
from secrets import token_urlsafe

from flask import url_for
from markupsafe import escape

from .crypto import validate_sid, ValidationError, REQUEST_INFO, DATA
from .errorhandler import TransferixException


def _safe_write(directory: Path, filename: str, content: str):
    temp_file = directory / f'{filename}.tmp'
    main_file = directory / filename
    try:
        with open(temp_file, 'w') as fp:
            fp.write(content)
        rename(temp_file, main_file)
    except OSError as exc:
        raise WriteFailure(msg='Writing file failed', status_code=409) from exc


def get_request_status(sid: str) -> str:
    with open(REQUEST_INFO / sid / 'status') as f:
        return f.read()


def generate_request_token(sid: str) -> str:
    token = token_urlsafe(32)
    _safe_write(directory=REQUEST_INFO / sid, filename='token', content=token)
    return token


def validate_request(sid: str | None, status: str):
    if sid is None:
        raise ValidationError(msg='sid missing', status_code=400)
    validate_sid(sid)
    if not (REQUEST_INFO / sid).is_dir():
        raise ValidationError(msg='invalid secret ID', status_code=400)
    if status == 'init' and not (REQUEST_INFO / sid / 'token').is_file():
        raise RequestStateException(msg='request is in wrong state', status_code=409)
    elif status == 'stored' and not (DATA / sid / 'secret').is_file():
        raise RequestStateException(msg='request is in wrong state', status_code=409)
    else:
        raise TransferixException(msg='Programming error. Please notify developers.', status_code=500)


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


class WriteFailure(TransferixException):
    pass


class RequestStateException(TransferixException):
    pass
