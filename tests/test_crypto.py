import pytest
from transferix.crypto import store, retrieve
from transferix.keys import generate_sid, generate_key, get_key_from_bytes, validate_key, validate_sid
from transferix.exceptions import TransferixException


def test_roundtrip():
    key_bytes = generate_key()
    key = get_key_from_bytes(key_bytes)
    sid = generate_sid()
    store(sid=sid, secret_bytes=b'geheim', key_bytes=key_bytes, filename=None)
    data, filename = retrieve(sid, key)
    assert data == b'geheim'
    assert filename is None


def test_second_retrieve_is_gone():
    key_bytes = generate_key()
    key = get_key_from_bytes(key_bytes)
    sid = generate_sid()
    store(sid=sid, secret_bytes=b'x', key_bytes=key_bytes, filename=None)
    retrieve(sid, key)
    with pytest.raises(TransferixException) as exc:
        retrieve(sid, key)
    assert exc.value.status_code == 410
