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
    file uploads. Please also set this limit in your reverse proxy configuration.
    Default is 10 MB.
-   `$TRANSFERIX_ENABLE_QR`: Set to an arbitrary value to show QR code
    of the share links. Needs `qrcode` Python library to be installed.
-   `$TRANSFERIX_ENABLE_API`: Set to an arbitrary value to enable API endpoints.
-   `$TRANSFERIX_AUTH_METHOD`: Activate authentication, possible values: `remote-user`, `oidc`
-   `$TRANSFERIX_OIDC_CLIENT_SECRETS`: Path to client_secrets.json for OIDC authentication
-   `$TRANSFERIX_PRIVILEGED_GROUPS`: Comma-separated list of privileged user groups

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
    └── <sid>/
        └── token          "<sid>|<key>" once the sender submitted
```

The encryption key is **never stored** – it exists only in the link that is
handed to the recipient. The server cannot decrypt a secret without that link.
Retrieval is destructive: the directory is renamed to `<sid>_locked`
(an atomic POSIX operation) and removed after the plaintext was read, so two
concurrent requests cannot retrieve the same secret twice.


## API reference

To enable the API set the environment variable `$TRANSFERIX_ENABLE_API`.

All API endpoints accept and return `application/json`. Errors always carry
`{"status": "error", "msg": "..."}`.


| Method | Path                 | Purpose                                                |
|-----|----------------------|--------------------------------------------------------|
| POST | `/api/new`           | Create a secret                                        |
| POST | `/api/reveal`        | Retrieve a text secret (file is not supported via API) |
| POST | `/api/request`       | Create a request                                       |
| POST | `/api/request/ready` | Poll for a requested secret                            |


### `POST /api/new`

Create a new secret. If `sid` and `key` are given, the secret is stored into a
pending request and only a confirmation is returned.

| Parameter | Required | Description                                             |
|-----------|----------|---------------------------------------------------------|
| `data`    | yes      | The secret itself (UTF-8 text)                          |
| `sid`     | no       | Secret ID, when answering a request                     |
| `key`     | no       | Key, when answering a request (required together with `sid`) |

```console
$ curl -sS -X POST https://transferix.example/api/new \
    -H 'Content-Type: application/json' \
    --data '{"data": "my secret"}'
{"secret_link": "https://transferix.example/get/ab12cd34/…", "status": "ok"}
```

Responds `201 Created`. Without `sid`/`key` the response contains `secret_link`;
with them it contains `msg` instead (`"secret stored"`).

Submitting into a request:

```console
$ curl -sS -X POST https://transferix.example/api/new \
    -H 'Content-Type: application/json' \
    --data '{"data": "my secret", "sid": "ab12cd34", "key": "…"}'
{"msg": "secret stored", "status": "ok"}
```

### `POST /api/reveal`

Retrieve a text secret. For secrets stored into a request, the `token` is
mandatory.

| Parameter | Required | Description                                  |
|-----------|----------|----------------------------------------------|
| `sid`     | yes      | Secret ID                                    |
| `key`     | yes      | Key from the secret link (43 characters)     |
| `token`   | no       | Request token, required for requested secrets |

```console
$ curl -sS -X POST https://transferix.example/api/reveal \
    -H 'Content-Type: application/json' \
    --data '{"sid": "ab12cd34", "key": "…"}'
{"secret": "my secret", "status": "ok"}
```

Retrieval is destructive: a second call returns `410 Gone`, regardless of
whether the caller processed the response. A wrong `key` returns `400` and also
destroys the secret. File secrets cannot be retrieved via the API and are
rejected with `400` – use the browser link instead.

### `POST /api/request`

Create a request. Takes no parameters.

```console
$ curl -sS -X POST https://transferix.example/api/request
{"key": "…",
 "request_link": "https://transferix.example/r/ab12cd34/…",
 "sid": "ab12cd34",
 "status": "added",
 "token": "…"}
```

Responds `201 Created`. Hand `request_link` to the person who should send you a
secret. Keep `sid` and `token` – they are needed to poll for the secret and to
retrieve it.

### `POST /api/request/ready`

Check whether the secret of a request has been submitted yet.

| Parameter | Required | Description    |
|-----------|----------|----------------|
| `sid`     | yes      | Secret ID      |
| `token`   | yes      | Request token  |

```console
$ curl -sS -X POST https://transferix.example/api/request/ready \
    -H 'Content-Type: application/json' \
    --data '{"sid": "ab12cd34", "token": "…"}'
{"msg": "secret has not been entered yet", "status": "waiting"}
```

Returns `200` with `status` set to `waiting` or `ready`. Once `ready`, fetch the
secret with `POST /api/reveal`, passing `sid`, `key` and `token`.
                                        |