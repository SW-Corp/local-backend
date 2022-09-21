from dataclasses import dataclass


@dataclass
class AuthException(Exception):
    detail: str = ""


class AuthenticatorServiceException(AuthException):
    pass


class InvalidCredentialsError(AuthException):
    pass


class InsufficientPermission(AuthException):
    pass
