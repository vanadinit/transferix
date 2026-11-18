#!/usr/bin/env python3
from os import getenv

from flask import Flask

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = int(getenv('TRANSFERIX_MAX_FILE_SIZE', 10_000_000))

from . import routes, api # noqa

if __name__ == '__main__':
    app.run(host='::')
