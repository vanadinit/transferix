from urllib.parse import urlsplit


def test_empty_textarea_is_400(client):
    r = client.post('/new', data={'data': ''})
    assert r.status_code == 400

def test_host_header_not_reflected(client):
    r = client.get('/request', headers={'Host': 'x"><script>alert(1)</script>'})
    assert '<script>alert(1)' not in r.get_data(as_text=True)

def test_share_and_reveal(client):
    r = client.post('/api/new', json={'data': 'geheim'})
    assert r.status_code == 201
    link = r.json['secret_link']
    path = urlsplit(link).path
    _, _, sid, key = path.split('/')
    assert client.get(r.json['secret_link']).status_code == 200
    assert client.post('/reveal', data={'sid': sid, 'key': key}).status_code == 200
