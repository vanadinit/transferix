from functools import wraps
from typing import Callable

from flask import request

from transferix.exceptions import TransferixException


def temp_access_granted() -> bool:
    raise NotImplementedError()


def login() -> dict:
    if not request.headers.get('Remote-User'):
        return {}

    return {
        'username': request.headers.get('Remote-User'),
        'groups': request.headers.get('Remote-Groups', '').split(';'),
    }


def auth_required(temp: bool = False, authorized_groups: list | None = None) -> Callable:
    def dec_auth_required(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            login_info = login()
            if not login_info:
                if temp and temp_access_granted():
                    # Temp access is only relevant for non-authenticated users
                    return func(*args, **kwargs)
                raise TransferixException('unauthenticated', 401)

            if authorized_groups is not None:
                for group in authorized_groups:
                    if group in login_info.get('groups', []):
                        return func(*args, **kwargs)
                raise TransferixException('forbidden', 403)
            return func(*args, **kwargs)

        return wrapper

    return dec_auth_required
