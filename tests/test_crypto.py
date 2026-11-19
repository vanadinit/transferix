import pytest
from transferix.crypto import store, retrieve, validate_key, validate_sid, OK, ALREADY_REVEALED
from transferix.errorhandler import TransferixException


def test_roundtrip():
    sid, key = store(b'geheim', None)
    data, filename, status = retrieve(sid, key)
    assert status == OK
    assert data == b'geheim'
    assert filename is None


def test_second_retrieve_is_gone():
    sid, key = store(b'x', None)
    retrieve(sid, key)
    _, _, status = retrieve(sid, key)
    assert status == ALREADY_REVEALED


@pytest.mark.parametrize('bad', ['', 'zu-kurz', 'x' * 44])
def test_invalid_key_raises(bad):
    with pytest.raises(TransferixException) as exc:
        validate_key(bad)
    assert exc.value.status_code == 400


@pytest.mark.parametrize('bad', ['../etc', 'abcd\n', 'toolong123'])
def test_invalid_sid_raises(bad):
    with pytest.raises(TransferixException):
        validate_sid(bad)
