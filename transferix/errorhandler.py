from flask import jsonify, request, render_template
from markupsafe import escape
from werkzeug.exceptions import HTTPException

from . import app
from .exceptions import TransferixException
from .language import _


def _error_response(msg: str, status_code: int):
    if request.is_json or request.path.startswith('/api/'):
        app.logger.debug('request type: API/JSON')
        return jsonify({'status': 'error', 'msg': msg}), status_code
    else:
        app.logger.debug('request type: Web')
        return render_template('message.html', msg={'head': 'error', 'content': msg}), status_code


@app.errorhandler(TransferixException)
def handle_transferix_exception(e: TransferixException):
    app.logger.debug(e, exc_info=e)
    return _error_response(e.msg, e.status_code)


@app.errorhandler(HTTPException)
def handle_http_exception(e: HTTPException):
    app.logger.debug(e, exc_info=e)
    return _error_response(f'{escape(e.name)}: {escape(e.description) or ""}', e.code or 500)


@app.errorhandler(Exception)
def handle_unknown_exception(e: Exception):
    app.logger.exception('Unhandled error', exc_info=e)
    return _error_response('internal error', 500)
