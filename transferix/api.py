import unicodedata
from base64 import b64decode
from os.path import isfile
from shutil import rmtree
from urllib.parse import quote

from flask import jsonify, make_response, redirect, request, url_for

from . import app
from .crypto import store, retrieve, validate_sid, validate_key, ALREADY_REVEALED, WRONG_KEY
from .request import is_valid_unused_rid, update_rid_info, create_rid, REQUEST_INFO


@app.route('/api/new', methods=['POST'])
@app.route('/api/new/<rid>', methods=['POST'])
def api_new(rid: str | None = None) -> tuple[str, int]:
    if not request.is_json:
        return 'No valid JSON request', 400
    rid = rid or request.json.get('rid')
    if rid and not is_valid_unused_rid(rid):
        return jsonify({
            'status': 'error',
            'msg': 'rid invalid',
        }), 400
    try:
        if 'data_base64' in request.json and 'filename' in request.json:
            secret_bytes = b64decode(request.json['data_base64'])
            filename = request.json['filename']
        else:
            secret_bytes = request.json['data'].encode('UTF-8')
            filename = None
    except Exception:
        return jsonify({
            'status': 'error',
            'msg': 'Data missing or invalid',
        }), 400

    if filename is None and len(secret_bytes.strip()) <= 0:
        return jsonify({
            'status': 'error',
            'msg': 'empty secret',
        }), 400

    sid, key = store(secret_bytes, filename)
    scheme = request.headers.get('x-forwarded-proto', 'http')
    host = request.headers.get('x-forwarded-host', request.headers['host'])
    sid_url = f'{scheme}://{host}/get/{sid}/{key}'

    if rid:
        if not update_rid_info(rid, sid_url):
            return jsonify({
                'status': 'error',
                'msg': 'rid missing or invalid',
            }), 400

        jsonify({
            'status': 'ok',
            'msg': 'secret stored',
        }), 201

    return jsonify({
        'status': 'ok',
        'secret_link': sid_url
    }), 201


@app.route('/api/reveal/<sid>/<key>', methods=['POST'])
def api_reveal(sid: str, key: str) -> tuple[str, int]:
    validate_key(key)
    validate_sid(sid)
    secret_bytes, filename, status = retrieve(sid, key)
    if status == ALREADY_REVEALED:
        return jsonify({
            'status': 'error',
            'msg': 'already revealed',
        }), 404
    elif status == WRONG_KEY:
        return jsonify({
            'status': 'error',
            'msg': 'wrong key',
        })
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
        return jsonify({
            'status': 'ok',
            'secret': secret,
        }), 410


@app.route('/api/request', methods=['POST'])
def api_request() -> tuple[str, int]:
    rid = create_rid()
    scheme = request.headers.get('x-forwarded-proto', 'http')
    host = request.headers.get('x-forwarded-host', request.headers['host'])

    return jsonify({
        'status': 'added',
        'request_link': f'{scheme}://{host}/{rid}',
        'consume_link': f'{scheme}://{host}/api/request/{rid}/consume',
    }), 201


@app.route('/api/request/<rid>/consume', methods=['POST'])
def api_request_consume(rid: int) -> tuple[str, int]:
    if isfile(REQUEST_INFO / rid / 'info'):
        with open(REQUEST_INFO / rid / 'info') as fp:
            sid_url = fp.read()
        rmtree(REQUEST_INFO / rid)
        return jsonify({
            'status': 'ready',
            'secret_link': sid_url,
        }), 200

    return jsonify({
        'status': 'waiting',
        'msg': 'secret has not been entered yet',
    }), 200
