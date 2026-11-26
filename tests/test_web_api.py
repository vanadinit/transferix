from urllib.parse import urlsplit


def test_unauthenticated_is_401(client):
    r = client.post('/new', data={'data': 'mysecret'})
    assert r.status_code == 401


def test_empty_textarea_is_400(client_auth):
    r = client_auth.post('/new', data={'data': ''})
    assert r.status_code == 400


def test_host_header_not_reflected(client_auth):
    r = client_auth.get('/request', headers={'Host': 'x"><script>alert(1)</script>'})
    assert '<script>alert(1)' not in r.get_data(as_text=True)


def test_share_and_reveal(client_auth):
    r = client_auth.post('/api/new', json={'data': 'geheim'})
    assert r.status_code == 201
    link = r.json['secret_link']
    path = urlsplit(link).path
    _, _, sid, key = path.split('/')
    assert client_auth.get(r.json['secret_link']).status_code == 200
    assert client_auth.post('/reveal', data={'sid': sid, 'key': key}).status_code == 200
