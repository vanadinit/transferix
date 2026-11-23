from flask import jsonify, request, url_for, Response

from . import app
from .crypto import retrieve, validate_key, ALREADY_REVEALED, WRONG_KEY, generate_sid, get_key_from_bytes, \
    generate_key
from .errorhandler import TransferixException
from .request import RequestStatus, update_request_status, generate_request_token
from .secrets import new_secret, validate_reveal, secret_ready


@app.route('/api/new', methods=['POST'])
def api_new() -> tuple[Response, int]:
    """
    API endpoint /api/new

    Create a new secret. If this is in response to a request, just OK is returned. Else the secret link is provided.

    params:
      data: secret data (required)
      sid: secret ID if coming from a request (optional)
      key: key if coming from a request (optional)
    :return:
    """
    if not request.is_json:
        raise TransferixException(msg='No valid JSON request', status_code=400)

    sid = request.json.get('sid')
    key = request.json.get('key')

    try:
        sid_url = new_secret(data=request.json['data'], sid=sid, key=key)
    except Exception as exc:
        raise TransferixException(msg='Data missing or invalid', status_code=400) from exc

    if sid:
        return jsonify({'status': 'ok', 'msg': 'secret stored'}), 201
    else:
        return jsonify({'status': 'ok', 'secret_link': sid_url}), 201


@app.route('/api/reveal', methods=['POST'])
def api_reveal() -> tuple[Response, int]:
    """
    API endpoint /api/reveal

    Reveal a secret. If this is in response to a request, the token must be provided.

    params:
      sid: secret ID (required)
      key: key (required)
      token: token (optional, required if coming from a request)
    :return:
    """
    sid = request.json['sid']
    key = request.json['key']
    token = request.json.get('token')

    is_request = validate_reveal(sid=sid, token=token)
    validate_key(key)
    secret_bytes, filename, status = retrieve(sid, key)
    if is_request:
        update_request_status(sid=sid, status=RequestStatus.REVEALED)
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
    """
    API endpoint /api/request

    Request a secret. The request link as well as the secret ID, the key and the token are returned.
    Give the request link to the person, you want the secret from.
    Use the request ready endpoint to check, if the secret was already entered.
    Use reveal endpoint with token to get the stored secret.

    no params
    :return:
    """
    sid = generate_sid(is_request=True)
    key = get_key_from_bytes(generate_key())
    token = generate_request_token(sid)
    update_request_status(sid=sid, status=RequestStatus.INIT)

    return jsonify({
        'status': 'added',
        'request_link': url_for('form_plain', sid=sid, key=key, _external=True),
        'sid': sid,
        'key': key,
        'token': token,
    }), 201


@app.route('/api/request/ready', methods=['POST'])
def api_request_ready() -> tuple[Response, int]:
    """
    API endpoint /api/request/ready

    Check if the secret of a request has been entered yet.

    params:
      sid: secret ID (required)
      token: token (required)
    :return:
    """
    sid = request.json['sid']
    token = request.json['token']

    if secret_ready(sid=sid, token=token):
        return jsonify({
            'status': 'ready',
            'msg': 'the secret has been stored and is ready to be retrieved',
        }), 200
    else:
        return jsonify({
            'status': 'waiting',
            'msg': 'secret has not been entered yet',
        }), 200
