from dataclasses import dataclass
from functools import wraps
from os import getenv
from typing import Callable

from flask import request, g

from . import app
from .exceptions import TransferixException

AUTH_METHOD = getenv('TRANSFERIX_AUTH_METHOD', None)


@dataclass
class LoginInfo:
    username: str
    groups: list


if AUTH_METHOD == 'oidc':
    from flask_oidc import OpenIDConnect

    oidc = OpenIDConnect(app)


    @oidc.require_login
    def login_oidc() -> LoginInfo | None:
        return LoginInfo(
            username=g.oidc_user.profile.get('email'),
            groups=g.oidc_user.profile.get('groups'),
        )
else:
    def login_oidc():
        raise NotImplementedError()


def temp_access_granted() -> bool:
    raise NotImplementedError()


def login_remote_user() -> LoginInfo | None:
    if not request.headers.get('Remote-User'):
        return None

    return LoginInfo(
        username=request.headers['Remote-User'],
        groups=request.headers.get('Remote-Groups', '').split(';'),
    )


def login() -> LoginInfo | None:
    match AUTH_METHOD:
        case 'oidc':
            return login_oidc()
        case 'remote_user':
            return login_remote_user()
        case None:
            return LoginInfo(username='anonymus', groups=[])
        case _:
            raise Exception('Unknown authentication method')


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
                    if group in login_info.groups:
                        return func(*args, **kwargs)
                raise TransferixException('forbidden', 403)
            return func(*args, **kwargs)

        return wrapper

    return dec_auth_required
