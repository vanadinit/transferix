from flask import jsonify, request, url_for, Response

from . import app
from .crypto import retrieve, validate_sid, validate_key, ALREADY_REVEALED, WRONG_KEY
from .errorhandler import TransferixException
from .request import create_rid
from .secrets import new_secret, consume_secret, NotReadyYetException


@app.route('/api/new', methods=['POST'])
@app.route('/api/new/<rid>', methods=['POST'])
def api_new(rid: str | None = None) -> tuple[Response, int]:
    if not request.is_json:
        raise TransferixException(msg='No valid JSON request', status_code=400)

    try:
        sid_url = new_secret(rid=rid or request.json.get('rid'), data=request.json['data'])
    except Exception as exc:
        raise TransferixException(msg='Data missing or invalid', status_code=400) from exc

    if rid:
        return jsonify({'status': 'ok', 'msg': 'secret stored'}), 201
    else:
        return jsonify({'status': 'ok', 'secret_link': sid_url}), 201


@app.route('/api/reveal/<sid>/<key>', methods=['POST'])
def api_reveal(sid: str, key: str) -> tuple[Response, int]:
    validate_key(key)
    validate_sid(sid)
    secret_bytes, filename, status = retrieve(sid, key)
    if status == ALREADY_REVEALED:
        raise TransferixException(msg='already revealed', status_code=410)
    elif status == WRONG_KEY:
        raise TransferixException(msg='wrong key', status_code=400)
    elif filename is not None:
        raise TransferixException(msg='retrieving file via API is not supported', status_code=400)
    else:
        secret = secret_bytes.decode('UTF-8')
        return jsonify({
            'status': 'ok',
            'secret': secret,
        }), 200


@app.route('/api/request', methods=['POST'])
def api_request() -> tuple[Response, int]:
    rid = create_rid()

    return jsonify({
        'status': 'added',
        'request_link': url_for('form_plain', rid=rid, _external=True),
        'consume_link': url_for('api_request_consume', rid=rid, _external=True),
    }), 201


@app.route('/api/request/<rid>/consume', methods=['POST'])
def api_request_consume(rid: str) -> tuple[Response, int]:
    try:
        sid, key = consume_secret(rid=rid)
        return jsonify({
            'status': 'ok',
            'secret_link': url_for('get', sid=sid, key=key, _external=True),
            'secret_api_link': url_for('api_reveal', sid=sid, key=key, _external=True),
        }), 200
    except NotReadyYetException:
        return jsonify({
            'status': 'waiting',
            'msg': 'secret has not been entered yet',
        }), 200
