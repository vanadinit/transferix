from unittest.mock import patch, NonCallableMagicMock


def test_404_non_existing(client):
    r = client.get('/some-path/does/not/exist')
    assert r.status_code == 404
    assert b'<h1>' in r.data


def test_405_api_wrong_method(client):
    r = client.get('/api/new')
    assert r.status_code == 405
    assert r.get_json()['status'] == 'error'


@patch('transferix.crypto.DATA', return_value='/tmp/notexisting')
def test_500_does_not_leak_details(mock_data: NonCallableMagicMock, client):
    r = client.post('/new', data={'data': 'x'})
    assert r.status_code == 500
    assert b'/tmp/' not in r.data
