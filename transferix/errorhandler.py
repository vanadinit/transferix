from flask import jsonify, request
from markupsafe import escape
from werkzeug.exceptions import HTTPException

from . import app
from .language import _
from .ui import html


class TransferixException(Exception):
    def __init__(self, msg: str, status_code: int):
        self.msg = msg
        self.status_code = status_code


def _error_response(msg: str, status_code: int):
    if request.is_json or request.path.startswith('/api/'):
        return jsonify({'status': 'error', 'msg': msg}), status_code
    else:
        return html(f'<h1>{_("error")}</h1><p>{_(msg)}</p>'), status_code


@app.errorhandler(TransferixException)
def handle_transferix_exception(e: TransferixException):
    return _error_response(e.msg, e.status_code)


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    return _error_response(f'{escape(e.name)}: {escape(e.description) or ""}', e.code or 500)


@app.errorhandler(Exception)
def handle_unknown_exception(e: Exception):
    app.logger.exception('Unhandled error', exc_info=e)
    return _error_response('internal error', 500)
