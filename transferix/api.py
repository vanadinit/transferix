from os.path import isfile, isdir
from shutil import rmtree

from flask import jsonify, request, url_for

from . import app
from .crypto import store, retrieve, validate_sid, validate_key, ALREADY_REVEALED, WRONG_KEY
from .request import is_valid_unused_rid, update_rid_info, create_rid, REQUEST_INFO, is_valid_rid


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
        secret_bytes = request.json['data'].encode('UTF-8')
    except Exception:
        return jsonify({
            'status': 'error',
            'msg': 'Data missing or invalid',
        }), 400

    if len(secret_bytes.strip()) <= 0:
        return jsonify({
            'status': 'error',
            'msg': 'empty secret',
        }), 400

    sid, key = store(secret_bytes, None)

    if rid:
        if not update_rid_info(rid=rid, sid=sid, key=key):
            return jsonify({
                'status': 'error',
                'msg': 'rid invalid',
            }), 400

        return jsonify({
            'status': 'ok',
            'msg': 'secret stored',
        }), 201

    return jsonify({
        'status': 'ok',
        'secret_link': url_for('get', sid=sid, key=key, _external=True),
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
        }), 410
    elif status == WRONG_KEY:
        return jsonify({
            'status': 'error',
            'msg': 'wrong key',
        }), 400
    elif filename is not None:
        return jsonify({
            'status': 'error',
            'msg': 'retrieving file via API is not supported',
        }), 400
    else:
        secret = secret_bytes.decode('UTF-8')
        return jsonify({
            'status': 'ok',
            'secret': secret,
        }), 200


@app.route('/api/request', methods=['POST'])
def api_request() -> tuple[str, int]:
    rid = create_rid()

    return jsonify({
        'status': 'added',
        'request_link': url_for('form_plain', rid=rid, _external=True),
        'consume_link': url_for('api_request_consume', rid=rid, _external=True),
    }), 201


@app.route('/api/request/<rid>/consume', methods=['POST'])
def api_request_consume(rid: int) -> tuple[str, int]:
    if not is_valid_rid(rid) or not isdir(REQUEST_INFO / rid):
        return jsonify({
            'status': 'error',
            'msg': 'rid missing or invalid',
        }), 400
    if isfile(REQUEST_INFO / rid / 'info'):
        with open(REQUEST_INFO / rid / 'info') as fp:
            sid, key = fp.read().split('|')
        rmtree(REQUEST_INFO / rid)
        return jsonify({
            'status': 'ok',
            'secret_link': url_for('get', sid=sid, key=key, _external=True),
            'secret_api_link': url_for('api_reveal', sid=sid, key=key, _external=True),
        }), 200

    return jsonify({
        'status': 'waiting',
        'msg': 'secret has not been entered yet',
    }), 200
