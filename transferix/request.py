from os import mkdir, rename, rmdir
from os.path import isdir, isfile
from pathlib import Path
from secrets import token_urlsafe

from .crypto import validate_sid, ValidationError, REQUEST_INFO
from .errorhandler import TransferixException


class RequestStatus:
    INIT = 'init'
    STORED = 'stored'
    REVEALED = 'revealed'


def _safe_write(directory: Path, filename: str, content: str):
    lock_dir = directory / 'lock'
    try:
        mkdir(lock_dir)
    except FileExistsError as e:
        raise WriteFailure(msg='Lock directory exists', status_code=400) from e

    temp_file = directory / f'{filename}.tmp'
    main_file = directory / filename
    try:
        with open(temp_file, 'w') as fp:
            fp.write(content)
        rename(temp_file, main_file)
    except OSError as e:
        raise WriteFailure(msg='Writing file failed', status_code=400) from e
    finally:
        rmdir(lock_dir)


def generate_request_token(sid: str) -> str:
    token = token_urlsafe(32)
    _safe_write(directory=REQUEST_INFO / sid, filename='token', content=token)
    return token


def validate_request(sid: str | None):
    if sid is None:
        raise ValidationError(msg='sid missing', status_code=400)
    validate_sid(sid)
    if not isdir(REQUEST_INFO / sid) or not isfile(REQUEST_INFO / sid / 'status'):
        raise ValidationError(msg='invalid secret ID', status_code=400)


def get_request_strs(sid: str | None, key: str | None) -> tuple[str, str]:
    if sid and key:
        validate_request(sid=sid)
        request_path = f'/{sid}/{key}'
        request_fields = f'<input name="sid" type="hidden" value="{sid}"><input name="key" type="hidden" value="{key}">'
    else:
        request_path = ''
        request_fields = ''

    return request_path, request_fields


def update_request_status(sid: str, status: str):
    _safe_write(directory=REQUEST_INFO / sid, filename='status', content=status)


class WriteFailure(TransferixException):
    pass
