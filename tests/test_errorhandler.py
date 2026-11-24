from pathlib import Path
from unittest.mock import patch, MagicMock

from werkzeug.exceptions import HTTPException

from transferix.exceptions import TransferixException


def test_error_handlers_registered(app):
    registered = app.error_handler_spec[None][None]
    assert TransferixException in registered
    assert HTTPException in registered
    assert Exception in registered


def test_404_non_existing(client):
    r = client.get('/some-path/does/not/exist')
    assert r.status_code == 404
    assert b'<h1>' in r.data


def test_405_api_wrong_method(client):
    r = client.get('/api/new')
    assert r.status_code == 405
    assert r.json['status'] == 'error'


@patch('transferix.crypto.DATA', new=Path('/tmp/notexisting'))
@patch('transferix.base.generate_sid', return_value='123456')
def test_500_does_not_leak_details(mock_generate_sid: MagicMock, client):
    r = client.post('/new', data={'data': 'x'})
    assert r.status_code == 500
    assert b'/tmp/' not in r.data
    assert b'internal error' in r.data
    mock_generate_sid.assert_called_once()
