from flask import jsonify, request

from . import app
from .language import _
from .ui import html


class TransferixException(Exception):
    def __init__(self, msg: str, status_code: int):
        self.msg = msg
        self.status_code = status_code


@app.errorhandler(TransferixException)
def handle_exception(e: TransferixException):
    if request.is_json:
        return jsonify({'status': 'error', 'msg': e.msg}), e.status_code
    else:
        return html(f'<h1>{_("error")}</h1><p>{_(e.msg)}</p>'), e.status_code


@app.errorhandler(Exception)
def handle_exception(e: Exception):
    if request.is_json:
        return jsonify({'status': 'error', 'msg': f'UNKNOWN Exception: {e}'}), 500
    else:
        return html(f'<h1>UNKNOWN Exception</h1><p>{e}</p>'), 500
