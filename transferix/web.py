import unicodedata
from os import getenv
from typing import Any
from urllib.parse import quote

from flask import make_response, request, url_for, render_template

from . import app
from .base import new_secret, validate_reveal, secret_ready, get_request_params
from .config import MAX_FILE_SIZE_HUMAN
from .crypto import retrieve, secret_exists_as_file
from .exceptions import TransferixException
from .keys import generate_request_token, generate_sid, generate_key, get_key_from_bytes, validate_key, validate_sid
from .language import _, get_lang
from .qr import qrcode_html


@app.context_processor
def inject_globals():
    return {
        '_': _,
        'lang': get_lang(),
        'css_url': getenv('TRANSFERIX_CSS', url_for('static', filename='style.css')),
        'logo_url': getenv('TRANSFERIX_LOGO', url_for('static', filename='logo.png')),
        'logo_dark_url': getenv('TRANSFERIX_LOGO_DARK', url_for('static', filename='logo-darkmode.png')),
        'logo_alt': getenv('TRANSFERIX_LABEL', 'my company'),
    }


@app.route('/')
@app.route('/r/<sid>/<key>')
def form_plain(sid: str | None = None, key: str | None = None) -> str | tuple[str, int]:
    request_path, request_info = get_request_params(sid=sid, key=key, target='form_file')
    return render_template(
        'form.html',
        form_type='plain',
        request_path=request_path,
        request_info=request_info,
    ), 200


@app.route('/file')
@app.route('/file/<sid>/<key>')
def form_file(sid: str | None = None, key: str | None = None) -> str | tuple[str, int]:
    request_path, request_info = get_request_params(sid=sid, key=key, target='form_plain')
    return render_template(
        'form.html',
        form_type='file',
        request_path=request_path,
        request_info=request_info,
        max_size_human=MAX_FILE_SIZE_HUMAN,
    ), 200


@app.route('/request')
def request_secret() -> Any:
    sid = generate_sid(is_request=True)
    key = get_key_from_bytes(generate_key())
    token = generate_request_token(sid)
    request_link = url_for('form_plain', sid=sid, key=key, _external=True)

    return render_template(
        'request.html',
        request_link=request_link,
        request_info={'sid': sid, 'key': key, 'token': token},
        qrcode_html=qrcode_html,
    ), 200


@app.route('/request/consume', methods=['POST'])
def request_consume() -> Any:
    sid = request.form.get('sid')
    key = request.form.get('key')
    token = request.form.get('token')

    if secret_ready(sid=sid, token=token):
        return get(sid=sid, key=key, token=token)
    else:
        return render_template('waiting.html'), 200


@app.route('/new', methods=['POST'])
def new() -> str | tuple[str, int] | Any:
    if request.is_json:
        raise TransferixException(msg='Please use API endpoint.', status_code=400)
    sid = request.form.get('sid')
    key = request.form.get('key')

    sid_url = new_secret(data=request.form.get('data'), sid=sid, key=key)
    if sid:
        return render_template(
            'message.html',
            msg={'head': 'rid secret stored', 'content': 'rid secret stored desc'},
        ), 201
    else:
        return render_template('share.html', sid_url=sid_url, qrcode_html=qrcode_html), 201


@app.route('/get/<sid>/<key>')
@app.route('/get/<sid>/<key>/<token>')
def get(sid: str | None, key: str | None, token: str | None = None) -> str | tuple[str, int]:
    # Force Flask to read remaining request body bytes to avoid TCP reset issues
    _dummy = len(request.data)  # noqa E841

    validate_key(key)
    validate_sid(sid)
    sid: str  # If validation raises no exception it must be str type. Define this explicit here to reduce IDE warnings.

    return render_template(
        'get.html',
        info={'sid': sid, 'key': key, 'token': token},
        download=secret_exists_as_file(sid),
    ), 200


@app.route('/reveal', methods=['POST'])
def reveal() -> str | tuple[str, int] | Any:
    sid = request.form['sid']
    key = request.form['key']
    token = request.form.get('token')

    validate_reveal(sid=sid, token=token)
    validate_key(key)
    secret_bytes, filename = retrieve(sid, key)
    if filename is not None:
        try:
            filename.encode("ascii")
        except UnicodeEncodeError:
            simple = unicodedata.normalize("NFKD", filename)
            simple = simple.encode("ascii", "ignore").decode("ascii")
            quoted = quote(filename, safe="!#$&+-.^_`|~")
            names = {"filename": simple, "filename*": f"UTF-8''{quoted}"}
        else:
            names = {"filename": filename}

        response = make_response(secret_bytes, 200)
        response.headers.set('Content-Disposition', 'attachment', **names)
        response.headers.set('Content-Type', 'application/octet-stream')
        response.headers.set('X-Content-Type-Options', 'nosniff')
        response.headers.set('Cache-Control', 'no-store')
        return response
    else:
        secret = secret_bytes.decode('UTF-8')
        lines = min(len(secret.split('\n')), 100)
        return render_template('reveal.html', lines=lines, secret=secret), 200
