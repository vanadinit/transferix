from flask import jsonify, request
from werkzeug.exceptions import HTTPException

from . import app
from .language import _
from .ui import html


class TransferixException(Exception):
    def __init__(self, msg: str, status_code: int):
        self.msg = msg
        self.status_code = status_code


@app.errorhandler(TransferixException)
def handle_transferix_exception(e: TransferixException):
    if request.is_json:
        return jsonify({'status': 'error', 'msg': e.msg}), e.status_code
    else:
        return html(f'<h1>{_("error")}</h1><p>{_(e.msg)}</p>'), e.status_code


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return e


@app.errorhandler(Exception)
def handle_unknown_exception(e: Exception):
    app.logger.exception('Unhandled error')
    if request.is_json:
        return jsonify({'status': 'error', 'msg': f'UNKNOWN Exception: {e}'}), 500
    else:
        return html(f'<h1>UNKNOWN Exception</h1><p>{e}</p>'), 500
