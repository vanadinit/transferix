import unicodedata
from base64 import b64decode
from os.path import isdir, isfile
from shutil import rmtree
from typing import Any
from urllib.parse import quote

from flask import jsonify, make_response, redirect, request, url_for
from markupsafe import escape

from . import app
from .crypto import store, retrieve, validate_key, validate_sid, secret_exists, ALREADY_REVEALED, WRONG_KEY
from .language import _
from .qr import qrcode_html
from .request import is_valid_rid, is_valid_unused_rid, create_rid, update_rid_info, REQUEST_INFO
from .ui import html, max_size_msg


@app.route('/')
@app.route('/<rid>')
def form_plain(rid: str | None = None) -> str | tuple[str, int]:
    if rid:
        if not is_valid_unused_rid(rid):
            return html(f'''                                                                                                                                                                                                          
                <h1>{_('error')}</h1>                                                                                                                                                                                                 
                <p>{_('rid missing or invalid')}</p>                                                                                                                                                                                  
            '''), 404
        rid_param = f'/{rid}'
        rid_field = f'<input name="rid" type="hidden" value="{rid}">'
    else:
        rid_param = ''
        rid_field = ''

    return html(f'''                                                                                                                                                                                                                  
        <h1>{_('share new secret')}</h1>                                                                                                                                                                                              
        <p>{_('welcome desc')}</p>                                                                                                                                                                                                    
        <p>{_('welcome maybe file').format(rid=rid_param)}{_("welcome maybe request") if not rid else ''}.</p>                                                                                                                        
        <form action="/new" method="post">                                                                                                                                                                                            
            <textarea name="data"></textarea>{rid_field}                                                                                                                                                                              
            <input type="submit" value="&#x1f517; {_('create link')}">                                                                                                                                                                
        </form>                                                                                                                                                                                                                       
    ''')


@app.route('/file')
@app.route('/file/<rid>')
def form_file(rid: str | None = None) -> str | tuple[str, int]:
    if rid:
        if not is_valid_unused_rid(rid):
            return html(f'''                                                                                                                                                                                                          
                <h1>{_('error')}</h1>                                                                                                                                                                                                 
                <p>{_('rid missing or invalid')}</p>                                                                                                                                                                                  
            '''), 404
        rid_param = rid
        rid_field = f'<input name="rid" type="hidden" value="{rid}">'
    else:
        rid_param = ''
        rid_field = ''

    max_size = f'<p>{max_size_msg()}</p>'
    return html(f'''                                                                                                                                                                                                                  
        <h1>{_('share new file')}</h1>                                                                                                                                                                                                
        <p>{_('welcome file')}</p>                                                                                                                                                                                                    
        <p>{_('welcome maybe text').format(rid=rid_param)}{_("welcome maybe request") if not rid else ''}.</p>                                                                                                                        
        {max_size}                                                                                                                                                                                                                    
        <form action="/new" method="post" enctype="multipart/form-data">                                                                                                                                                              
            <input type="file" name="file">{rid_field}                                                                                                                                                                                
            <input type="submit" value="&#x1f517; {_('create link')}">                                                                                                                                                                
        </form>                                                                                                                                                                                                                       
    ''')


@app.route('/request')
def request_secret_init() -> Any:
    rid = create_rid()
    return redirect(url_for('request_secret', rid=rid))


@app.route('/request/<rid>')
def request_secret(rid: str) -> str | tuple[str, int]:
    if not is_valid_rid(rid) or not isdir(REQUEST_INFO / rid):
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('error')}</h1>                                                                                                                                                                                                     
            <p>{_('rid missing or invalid')}</p>                                                                                                                                                                                      
        '''), 404

    scheme = request.headers.get('x-forwarded-proto', 'http')
    host = request.headers.get('x-forwarded-host', request.headers['host'])

    request_link = f'{scheme}://{host}/{rid}'

    consume_url = url_for('request_consume', rid=rid)

    return html(f'''                                                                                                                                                                                                                  
        <h1>{_('request')}</h1>                                                                                                                                                                                                       
        <p>{_('request desc')}</p>                                                                                                                                                                                                    
        {qrcode_html(request_link)}                                                                                                                                                                                                                 
        <p>Request-Link: <input id="copytarget" type="text" value="{request_link}"></p>                                                                                                                                               
        <p><span class="button" onclick="copy()">&#x1f4cb; {_('clip')}</span></p>                                                                                                                                                     
        <hr>                                                                                                                                                                                                                          
        <p><a href="{consume_url}" class="button">{_('go to receive')}</a></p>                                                                                                                                                        
    '''), 200


@app.route('/request/<rid>/consume')
def request_consume(rid: str) -> str | tuple[str, int] | Any:
    if not is_valid_rid(rid) or not isdir(REQUEST_INFO / rid):
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('error')}</h1>                                                                                                                                                                                                     
            <p>{_('rid missing or invalid')}</p>                                                                                                                                                                                      
        '''), 400

    if isfile(REQUEST_INFO / rid / 'info'):
        with open(REQUEST_INFO / rid / 'info') as fp:
            sid_url = fp.read()
        rmtree(REQUEST_INFO / rid)
        return redirect(sid_url)

    return html(f'''                                                                                                                                                                                                                  
        <h1>{_('waiting for secret')}</h1>                                                                                                                                                                                            
        <p>{_('waiting for secret desc')}</p>                                                                                                                                                                                         
        <p><label><input type="checkbox" id="autoReloadToggle" checked> {_('autoreload')}</label></p>                                                                                                                                 
    '''), 200


@app.route('/new', methods=['POST'])
@app.route('/new/<rid>', methods=['POST'])
def new(rid: str | None = None) -> str | tuple[str, int] | Any:
    rid = rid or request.form.get('rid') or (request.json.get('rid') if request.is_json else None)
    if rid:
        if not is_valid_unused_rid(rid):
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'msg': 'rid missing or invalid',
                }), 400
            else:
                return html(f'''                                                                                                                                                                                                      
                    <h1>{_('error')}</h1>                                                                                                                                                                                             
                    <p>{_('rid missing or invalid')}</p>                                                                                                                                                                              
                '''), 400

    try:
        if request.is_json:
            if 'data_base64' in request.json and 'filename' in request.json:
                secret_bytes = b64decode(request.json['data_base64'])
                filename = request.json['filename']
            else:
                secret_bytes = request.json['data'].encode('UTF-8')
                filename = None
        elif request.form.get('data'):
            secret_bytes = request.form['data'].encode('UTF-8')
            filename = None
        else:
            secret_bytes = request.files['file'].read()
            filename = request.files['file'].filename
    except Exception:
        return 'Garbage', 400

    if filename is None and len(secret_bytes.strip()) <= 0:
        if request.is_json:
            return jsonify({
                'status': 'error',
                'msg': 'empty secret',
            }), 400
        else:
            return redirect(url_for('form_plain'))

    sid, key = store(secret_bytes, filename)
    scheme = request.headers.get('x-forwarded-proto', 'http')
    host = request.headers.get('x-forwarded-host', request.headers['host'])
    sid_url = f'{scheme}://{host}/get/{sid}/{key}'

    if rid:
        if not update_rid_info(rid, sid_url):
            if request.is_json:
                return jsonify({
                    'status': 'error',
                    'msg': 'rid missing or invalid',
                }), 400
            else:
                return html(f'''                                                                                                                                                                                                      
                    <h1>{_('error')}</h1>                                                                                                                                                                                             
                    <p>{_('rid missing or invalid')}</p>                                                                                                                                                                              
                '''), 400

        return html(f'''                                                                                                                                                                                                              
            <h1>{_('rid secret stored')}</h1>                                                                                                                                                                                         
            <p>{_('rid secret stored desc')}</p>                                                                                                                                                                                      
        '''), 201

    if request.is_json:
        return jsonify({
            'status': 'ok',
            'secret_link': sid_url
        }), 201
    else:
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('share this')}</h1>                                                                                                                                                                                                
            <p>{_('share this desc')}</p>                                                                                                                                                                                             
            {qrcode_html(sid_url)}                                                                                                                                                                                                             
            <p><input id="copytarget" type="text" value="{sid_url}"></p>                                                                                                                                                              
            <p><span class="button" onclick="copy()">&#x1f4cb; {_('clip')}</span></p>                                                                                                                                                 
        '''), 201


@app.route('/get/<sid>/<key>')
def get(sid: str, key: str) -> str | tuple[str, int]:
    # Force Flask to read remaining request body bytes to avoid TCP reset issues
    _dummy = len(request.data)

    validate_key(key)
    validate_sid(sid)
    exists, as_file = secret_exists(sid)
    if exists:
        if as_file:
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
            <form id="form" action="/reveal/{sid}/{key}" method="post">                                                                                                                                                               
                <input name="compat" type="hidden" value="lynx needs this">                                                                                                                                                           
                <input type="submit" value="{icon} {btn}" {btn_js}>                                                                                                                                                                   
            </form>                                                                                                                                                                                                                   
        ''')
    else:
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('error')}</h1>                                                                                                                                                                                                     
            {_('already revealed')}                                                                                                                                                                                                   
        ''')


@app.route('/reveal/<sid>/<key>', methods=['POST'])
def reveal(sid: str, key: str) -> str | tuple[str, int] | Any:
    validate_key(key)
    validate_sid(sid)
    secret_bytes, filename, status = retrieve(sid, key)
    if status == ALREADY_REVEALED:
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('error')}</h1>                                                                                                                                                                                                     
            {_('already revealed')}                                                                                                                                                                                                   
        '''), 404
    elif status == WRONG_KEY:
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('error')}</h1>                                                                                                                                                                                                     
            <p>{_('wrong key')}</p>                                                                                                                                                                                                   
        '''), 404
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
        return response
    else:
        secret = secret_bytes.decode('UTF-8')
        lines = min(len(secret.split('\n')), 100)
        return html(f'''                                                                                                                                                                                                              
            <h1>{_('secret')}</h1>                                                                                                                                                                                                    
            <p>{_('your secret')}</p>                                                                                                                                                                                                 
            <textarea rows="{lines}" id="copytarget">{escape(secret)}</textarea>                                                                                                                                                      
            <p><span class="button" onclick="copy()">&#x1f4cb; {_('clip')}</span></p>                                                                                                                                                 
        '''), 410
