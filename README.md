transferix
===========

A simple tool for transferring secrets which will self-destruct on retrieval.

This is a fork of https://github.com/seibert-media/fluesterfix
implementing additional features like requesting secrets and using QR-Codes.

## Installation

You need:

-   Python 3
-   Flask
-   PyNaCl
-   shred, usually from GNU coreutils

You don’t need a database. However, this program expects to operate on a
file system that guarantees POSIX semantics.


## Running

For development and testing, just run:

    $ flask --app transferix:app run --debug

For anything else, set up a WSGI environment. A Python package can be
installed using `pip install -e .`.

Use the following environment variables:

-   `$TRANSFERIX_DATA`: The directory where data will be stored. Must
    exist prior to running the program. Should be created by sysadmin
    with correct permissions. Defaults to `/tmp` for quick tests.
-   `$TRANSFERIX_CSS`: URL to custom CSS to use, defaults to
    `style.css`.
-   `$TRANSFERIX_LOGO`: URL to custom logo to use, defaults to
    `logo.png`.
-   `$TRANSFERIX_LOGO_DARK`: URL to custom logo in dark mode to use,
    defaults to `logo-darkmode.png`.
-   `$TRANSFERIX_LABEL`: Custom alternative name for logo, defaults to
    `my company`.
-   `$TRANSFERIX_MAX_FILE_SIZE`: Maximum allowed size (in bytes) for
    file uploads. The actual filtering must be done in your reverse
    proxy; this variable only displays that limit. Unset by default.
-   `$TRANSFERIX_ENABLE_QR`: Set to an arbitrary value to show QR code
    of the share links. Needs `qrcode` Python library to be installed.
-   `$TRANSFERIX_ENABLE_API`: Set to an arbitrary value to enable API endpoints.

The program does not automatically remove secrets or requests which have
never been retrieved or consumed. You might want to install a cron job on your
system to remove old directories in `$TRANSFERIX_DATA` (including those in
`$TRANSFERIX_DATA/request_infos`) based on their mtime.


## How it works

**transferix** keeps everything on the file system – there is no database.

```
$TRANSFERIX_DATA/
├── <sid>/                 one directory per stored secret
│   ├── secret             NaCl SecretBox ciphertext
│   └── filename           original file name (only for file uploads)
└── request_infos/
    └── <rid>/
        ├── info           "<sid>|<key>" once the sender submitted
        └── lock           short-lived lock directory
```

The encryption key is **never stored** – it exists only in the link that is
handed to the recipient. The server cannot decrypt a secret without that link.
Retrieval is destructive: the directory is renamed to `<sid>_locked`
(an atomic POSIX operation) and removed after the plaintext was read, so two
concurrent requests cannot retrieve the same secret twice.

## Standard Endpoints

| Method | Path | Purpose |
|-----| ---- | ------- |
| GET | `/`            | Form: share a text secret |
| GET | `/<rid>`       | Form: submit a secret into a pending request |
| GET | `/file`, `/file/<rid>` | Form: share a file |
| POST | `/new`, `/new/<rid>` | Browser form target (HTML response) |
| GET | `/get/<sid>/<key>` | Confirmation page ("reveal?") |
| POST | `/reveal/<sid>/<key>` | Destroys the secret, returns text or file |
| GET | `/request`     | Creates a request, redirects to `/request/<rid>` |
| GET | `/request/<rid>` | Shows the request link (and QR code) to the sender |
| GET | `/request/<rid>/consume` | Waits for / fetches the requested secret (browser) |

> **Note:** the browser endpoints under `/new` and `/reveal` return HTML and are
> meant for the web UI. Programmatic clients should use `/api/*` (see below) exclusively.


## API reference

To enable the API set the environment variable `$TRANSFERIX_ENABLE_API`.

All API endpoints accept and return `application/json`. Errors always carry
`{"status": "error", "msg": "..."}`.


| Method | Path | Purpose |
|-----| ---- | ------- |
| POST | `/api/new`     | Create a secret, JSON |
| POST | `/api/new/<rid>` | Submit a secret into a pending request, JSON |
| POST | `/api/reveal/<sid>/<key>` | Retrieve a text secret, JSON |
| POST | `/api/request` | Create a request, JSON |
| POST | `/api/request/<rid>/consume` | Poll for / fetch the requested secret, JSON |


### `POST /api/new`

```console
$ curl -sS -X POST https://transferix.example/api/new \
    -H 'Content-Type: application/json' \
    --data '{"data": "my secret"}'
{"secret_link": "https://transferix.example/get/ab12/…", "status": "ok"}
```

### `POST /api/reveal/<sid>/<key>`

```console
$ curl -sS -X POST https://transferix.example/api/reveal/ab12/…
{"secret": "my secret", "status": "ok"}
```

A second call returns `410 Gone` – the secret is destroyed after the first
successful retrieval, regardless of whether the caller processed the response.

### `POST /api/request` / `POST /api/request/<rid>/consume`

```console
$ curl -sS -X POST https://transferix.example/api/request
{"consume_link": "…/api/request/<rid>/consume",
 "request_link": "…/<rid>",
 "status": "added"}

$ curl -sS -X POST https://transferix.example/api/request/<rid>/consume
{"status": "waiting", "msg": "secret has not been entered yet"}
```

`request_link` is handed to the person who should send you a secret. Poll
`consume_link` until `status` is `ok`; you then receive `secret_link` (for the
browser) and `secret_api_link` (for `POST`-based retrieval). Polling is
unauthenticated – anyone holding `consume_link` can fetch the secret.
