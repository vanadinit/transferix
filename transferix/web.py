import unicodedata
from typing import Any
from urllib.parse import quote

from flask import make_response, request, url_for
from markupsafe import escape

from . import app
from .crypto import retrieve, validate_key, validate_sid, secret_exists_as_file, ALREADY_REVEALED, WRONG_KEY, \
    generate_sid, generate_key, get_key_from_bytes
from .errorhandler import TransferixException
from .language import _
from .qr import qrcode_html
from .request import get_request_strs, generate_request_token, update_request_status, RequestStatus
from .secrets import new_secret, validate_reveal, secret_ready
from .ui import html, max_size_msg


@app.route('/')
@app.route('/<sid>/<key>')
def form_plain(sid: str | None = None, key: str | None = None) -> str | tuple[str, int]:
    request_path, request_fields = get_request_strs(sid=sid, key=key)

    return html(f'''
        <h1>{_('share new secret')}</h1>
        <p>{_('welcome desc')}</p>
        <p>{_('welcome maybe file').format(request_path=request_path)}{_("welcome maybe request") if not request_path else ''}.</p>
        <form action="/new" method="post">
            <textarea name="data"></textarea>{request_fields}
            <input type="submit" value="&#x1f517; {_('create link')}">
        </form>
    ''')


@app.route('/file')
@app.route('/file/<sid>/<key>')
def form_file(sid: str | None = None, key: str | None = None) -> str | tuple[str, int]:
    request_path, request_fields = get_request_strs(sid=sid, key=key)

    max_size = f'<p>{max_size_msg()}</p>'
    return html(f'''
        <h1>{_('share new file')}</h1>
        <p>{_('welcome file')}</p>
        <p>{_('welcome maybe text').format(request_path=request_path.lstrip('/'))}{_("welcome maybe request") if not request_path else ''}.</p>
        {max_size}
        <form action="/new" method="post" enctype="multipart/form-data">
            <input type="file" name="file">{request_fields}
            <input type="submit" value="&#x1f517; {_('create link')}">
        </form>
    ''')


@app.route('/request')
def request_secret() -> Any:
    sid = generate_sid(is_request=True)
    key = get_key_from_bytes(generate_key())
    token = generate_request_token(sid)
    request_link = url_for('form_plain', sid=sid, key=key, _external=True)

    return html(f'''
        <h1>{_('request')}</h1>
        <p>{_('request desc')}</p>
        {qrcode_html(request_link)}
        <p>Request-Link: <input id="copytarget" type="text" value="{request_link}"></p>
        <p><span class="button" onclick="copy()">&#x1f4cb; {_('clip')}</span></p>
        <hr>
        <p>
        <form action="/request/consume" method="post" enctype="multipart/form-data">
            <input type="submit" value="&#x1f517; {_('go to receive')}">
            <input name="sid" type="hidden" value="{sid}">
            <input name="key" type="hidden" value="{key}">
            <input name="token" type="hidden" value="{token}">
        </form>
        </p>
    '''), 200


@app.route('/request/consume', methods=['POST'])
def request_consume() -> Any:
    sid = request.form['sid']
    key = request.form['key']
    token = request.form['token']

    if secret_ready(sid=sid, token=token):
        return get(sid=sid, key=key, token=token)
    else:
        return html(f'''
            <h1>{_('waiting for secret')}</h1>
            <p>{_('waiting for secret desc')}</p>
            <p><label><input type="checkbox" id="autoReloadToggle" checked> {_('autoreload')}</label></p>
        '''), 200


@app.route('/new', methods=['POST'])
def new() -> str | tuple[str, int] | Any:
    if request.is_json:
        raise TransferixException(msg='Please use API endpoint.', status_code=400)
    sid = request.form.get('sid')
    key = request.form.get('key')

    sid_url = new_secret(data=request.form.get('data'), sid=sid, key=key)
    if sid:
        return html(f'''
            <h1>{_('rid secret stored')}</h1>
            <p>{_('rid secret stored desc')}</p>
        '''), 201
    else:
        return html(f'''
            <h1>{_('share this')}</h1>
            <p>{_('share this desc')}</p>
            {qrcode_html(sid_url)}
            <p><input id="copytarget" type="text" value="{sid_url}" /></p>
            <p><span class="button" onclick="copy()">&#x1f4cb; {_('clip')}</span></p>
        '''), 201


@app.route('/get/<sid>/<key>')
@app.route('/get/<sid>/<key>/<token>')
def get(sid: str, key: str, token: str | None = None) -> str | tuple[str, int]:
    # Force Flask to read remaining request body bytes to avoid TCP reset issues
    _dummy = len(request.data)  # noqa E841

    validate_key(key)
    validate_sid(sid)

    hidden_token_str = f'<input name="token" type="hidden" value="{escape(token)}">' if token else ''

    if secret_exists_as_file(sid):
        h1 = _('download?')
        btn = _('download!')
        btn_js = (
                'id="button" '
                'onclick="'
                'document.getElementById(\'button\').disabled = true;'
                'document.getElementById(\'button\').value = \'' +
                _('download done') +
                '\';'
                'document.getElementById(\'form\').submit();'
                '"'
        )
        icon = '&#x1f4be;'
    else:
        h1 = _('reveal?')
        btn = _('reveal!')
        btn_js = ''
        icon = '&#x1f50d;'

    return html(f'''
        <h1>{h1}</h1>
        <p>{_('only once')}</p>
        <form id="form" action="/reveal" method="post">
            <input name="compat" type="hidden" value="lynx needs this">
            <input name="sid" type="hidden" value="{escape(sid)}">
            <input name="key" type="hidden" value="{escape(key)}">
            {hidden_token_str}
            <input type="submit" value="{icon} {btn}" {btn_js}>
        </form>
    '''), 200


@app.route('/reveal', methods=['POST'])
def reveal() -> str | tuple[str, int] | Any:
    sid = request.form['sid']
    key = request.form['key']
    token = request.form.get('token')

    validate_reveal(sid=sid, token=token)
    validate_key(key)
    secret_bytes, filename, status = retrieve(sid, key)
    if status == ALREADY_REVEALED:
        raise TransferixException(msg='already revealed', status_code=410)
    elif status == WRONG_KEY:
        raise TransferixException(msg='wrong key', status_code=400)
    elif filename is not None:
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
        return html(f'''
            <h1>{_('secret')}</h1>
            <p>{_('your secret')}</p>
            <textarea rows="{lines}" id="copytarget">{escape(secret)}</textarea>
            <p><span class="button" onclick="copy()">&#x1f4cb; {_('clip')}</span></p>
        '''), 200
