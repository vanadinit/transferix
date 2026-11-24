class TransferixException(Exception):
    def __init__(self, msg: str, status_code: int):
        self.msg = msg
        self.status_code = status_code


class RequestStateException(TransferixException):
    pass


class ValidationError(TransferixException):
    pass


class WriteFailure(TransferixException):
    pass
