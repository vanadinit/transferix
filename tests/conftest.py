import os
import shutil
import tempfile
from pathlib import Path

import pytest

_TMP = Path(tempfile.mkdtemp(prefix='transferix-test-'))
os.environ['TRANSFERIX_DATA'] = str(_TMP)
os.environ['TRANSFERIX_ENABLE_API'] = '1'
os.environ['TRANSFERIX_MAX_FILE_SIZE'] = '1000000'

from transferix import app as flask_app  # noqa: E402


def pytest_sessionfinish(session, exitstatus):
    shutil.rmtree(_TMP, ignore_errors=True)


@pytest.fixture()
def app():
    return flask_app


@pytest.fixture(autouse=True)
def clean_data():
    """Leeres Datenverzeichnis pro Test."""
    for entry in _TMP.iterdir():
        if entry.is_dir():
            shutil.rmtree(entry)
        else:
            entry.unlink()
    yield


@pytest.fixture()
def client():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        yield c


@pytest.fixture()
def client_auth():
    flask_app.config['TESTING'] = True
    with flask_app.test_client() as c:
        c.environ_base['HTTP_REMOTE_USER'] = 'testuser'
        c.environ_base['HTTP_REMOTE_GROUPS'] = 'transferix;groupa'
        yield c
