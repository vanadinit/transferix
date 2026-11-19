from urllib.parse import urlsplit


def test_empty_textarea_is_400(client):
    r = client.post('/new', data={'data': ''})
    assert r.status_code == 400


def test_share_and_reveal(client):
    # FIXME: Mixed web and api
    r = client.post('/api/new', json={'data': 'geheim'})
    assert r.status_code == 201
    link = r.get_json()['secret_link']
    path = urlsplit(link).path
    assert client.get(path).status_code == 200
    assert client.post(path.replace('/get/', '/reveal/')).status_code == 200
