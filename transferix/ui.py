from os import environ

from flask import url_for

from .config import MAX_FILE_SIZE
from .language import get_lang, _


def html(body: str) -> str:
    css_url = environ.get('TRANSFERIX_CSS', url_for('static', filename='style.css'))
    logo_url = environ.get('TRANSFERIX_LOGO', url_for('static', filename='logo.png'))
    logo_dark_url = environ.get('TRANSFERIX_LOGO_DARK', url_for('static', filename='logo-darkmode.png'))
    logo_alt = environ.get('TRANSFERIX_LABEL', 'my company')

    return f'''<!DOCTYPE html>
<html lang="{get_lang()}">
    <head>
        <meta charset="UTF-8" />
        <meta name="viewport" content="width=device-width,initial-scale=1.0" />
        <title>{_('title')}</title>
        <link rel="stylesheet" href="{css_url}" type="text/css" />
        <script src="{url_for('static', filename='clipboard.js')}"></script>
        <script src="{url_for('static', filename='reload.js')}"></script>
    </head>
    <body>
        <a href="/" class="headerlink">
            <picture>
                <source srcset="{logo_dark_url}" media="(prefers-color-scheme: dark)" />
                <img src="{logo_url}" id="logo" alt="{logo_alt}" />
            </picture>
        </a>
        {body}
    </body>
</html>'''


def max_size_msg() -> str:
    for div, suff in (
            (1_000_000_000, 'GB'),
            (1_000_000, 'MB'),
            (1_000, 'kB'),
    ):
        if MAX_FILE_SIZE >= div:
            max_size_human = f'{MAX_FILE_SIZE // div} {suff}'
            break
    else:
        max_size_human = f'{MAX_FILE_SIZE} Bytes'

    return f'{_("welcome file max")}: {max_size_human}.'
