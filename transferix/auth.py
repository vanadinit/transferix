from dataclasses import dataclass, field
from functools import wraps
from os import getenv
from typing import Callable

from flask import request, g

from . import app
from .exceptions import TransferixException

AUTH_METHOD = getenv('TRANSFERIX_AUTH_METHOD', None)
PRIVILEGED_GROUPS = getenv('TRANSFERIX_PRIVILEGED_GROUPS')

if AUTH_METHOD == 'oidc':
    from flask_oidc import OpenIDConnect

    app.config['OIDC_CLIENT_SECRETS'] = getenv('TRANSFERIX_OIDC_CLIENT_SECRETS')
    oidc = OpenIDConnect(app)


@dataclass
class LoginInfo:
    logged_in: bool = False
    username: str = ''
    email: str = ''
    groups: list = field(default_factory=list)

    @property
    def is_privileged(self) -> bool:
        if PRIVILEGED_GROUPS is not None:
            for group in PRIVILEGED_GROUPS.split(','):
                if group.strip() in self.groups:
                    return True
        return False

    def login(self):
        # No special login method defined => login cannot be performed
        raise TransferixException('unauthenticated', 401)

    def check_authorized(self, authorized_groups: list | None):
        if authorized_groups is not None:
            for group in authorized_groups:
                if group in self.groups:
                    return
            raise TransferixException('forbidden', 403)


class HeaderLoginInfo(LoginInfo):
    def __init__(self):
        if request.headers.get('Remote-User'):
            super().__init__(
                logged_in=True,
                username=request.headers['Remote-User'],
                groups=request.headers.get('Remote-Groups', '').split(';')
            )
        else:
            super().__init__()


class OIDCLoginInfo(LoginInfo):
    def __init__(self):
        if oidc.user_loggedin:
            super().__init__(
                logged_in=True,
                username=g.oidc_user.profile.get('name'),
                email=g.oidc_user.profile.get('email'),
                groups=g.oidc_user.profile.get('groups'),
            )
            app.logger.debug(dir(g.oidc_user.profile))
        else:
            super().__init__()

    def login(self):
        return oidc.redirect_to_auth_server()


def get_login_info() -> LoginInfo:
    match AUTH_METHOD:
        case 'oidc':
            return OIDCLoginInfo()
        case 'remote_user':
            return HeaderLoginInfo()
        case None:
            return LoginInfo(logged_in=True, username='anonymus', groups=[])
        case _:
            raise Exception('Unknown authentication method')


def temp_access_granted() -> bool:
    raise NotImplementedError()


def request_toggle() -> bool:
    login_info = get_login_info()
    return bool(AUTH_METHOD and login_info and login_info.is_privileged)


def auth_required(temp: bool = False, authorized_groups: list | None = None) -> Callable:
    def dec_auth_required(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            login_info = get_login_info()
            app.logger.debug(login_info)
            if not login_info.logged_in:
                if temp and temp_access_granted():
                    # Temp access is only relevant for non-authenticated users
                    return func(*args, **kwargs)
                return login_info.login()

            login_info.check_authorized(authorized_groups)
            return func(*args, **kwargs)

        return wrapper

    return dec_auth_required
