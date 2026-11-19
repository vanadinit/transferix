#!/usr/bin/env python3
from os import getenv

from flask import Flask
from werkzeug.middleware.proxy_fix import ProxyFix

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
app.config['MAX_CONTENT_LENGTH'] = int(getenv('TRANSFERIX_MAX_FILE_SIZE', 10_000_000))

from . import web  # noqa

if getenv('TRANSFERIX_ENABLE_API'):
    from . import api  # noqa

if __name__ == '__main__':
    app.run(host='::')
