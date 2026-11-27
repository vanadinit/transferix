#!/usr/bin/env python3
from os import getenv
from secrets import token_hex

from flask import Flask, Response
from werkzeug.middleware.proxy_fix import ProxyFix

from .config import MAX_FILE_SIZE

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE
app.config["SECRET_KEY"] = token_hex(24)


@app.after_request
def _security_headers(response: Response):
    response.headers.setdefault('Referrer-Policy', 'no-referrer')
    response.headers.setdefault('X-Content-Type-Options', 'nosniff')
    response.headers.set('Cache-Control', 'no-store')
    return response


from . import web, errorhandler  # noqa

if getenv('TRANSFERIX_ENABLE_API'):
    from . import api  # noqa

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)
