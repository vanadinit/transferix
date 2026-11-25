from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest

from transferix.config import DATA, REQUEST_INFO
from transferix.exceptions import ValidationError
from transferix.keys import generate_sid, validate_sid, generate_key, get_key_from_bytes, validate_key, \
    get_bytes_from_key


@patch('transferix.keys.makedirs')
@patch('transferix.keys.mkdir')
def test__generate_sid(mock_mkdir: MagicMock, mock_makedirs: MagicMock):
    sid = generate_sid(is_request=True)
    validate_sid(sid)
    assert mock_makedirs.call_count == 2
    mock_makedirs.assert_has_calls([
        call(DATA, mode=0o700, exist_ok=True),
        call(REQUEST_INFO, mode=0o700, exist_ok=True),
    ], any_order=True)
    assert mock_mkdir.call_count == 2
    mock_mkdir.assert_has_calls([
        call(DATA / sid, mode=0o700),
        call(REQUEST_INFO / sid, mode=0o700)
    ], any_order=True)


@pytest.mark.parametrize('bad', ['\\_123456', 'abcd\n231', '<script>'])
def test__validate_sid_fails(bad: str):
    with pytest.raises(ValidationError) as exc:
        validate_sid(bad)
    assert exc.value.status_code == 400


def test__generate_key():
    key_bytes = generate_key()
    key = get_key_from_bytes(key_bytes=key_bytes)
    validate_key(key)
    assert get_bytes_from_key(key) == key_bytes


@pytest.mark.parametrize('bad', ['\\_123456', '<script>alert("Ahh evil things")</script>'])
def test__validate_key_fails(bad: str):
    with pytest.raises(ValidationError) as exc:
        validate_sid(bad)
    assert exc.value.status_code == 400
