import json
from dataclasses import dataclass
from http.client import HTTPConnection

import jwt

from ..exceptions import AuthenticatorServiceException, InvalidCredentialsError


@dataclass
class AuthConfig:
    port: int
    addr: str
    secret_key: str
    mode: str
    auth_ttl: int


@dataclass
class AuthController:
    config: AuthConfig

    def generateCookie(self, username: str) -> str:
        username_jwt = jwt.encode(
            {"username": username}, self.config.secret_key, algorithm="HS256"
        )
        return f"Authorization={username_jwt}; HttpOnly; Max-Age={self.config.auth_ttl}"

    def call_authenticator(self, method, path, body):
        httpsConnection = HTTPConnection(self.config.addr, self.config.port)
        body = json.dumps(body)

        try:
            httpsConnection.request(method, path, body)
        except Exception:
            raise AuthenticatorServiceException("Can't connect to authenticator")
        response = httpsConnection.getresponse()
        if response.status == 200:
            return response.read().decode()
        if response.status == 401:
            raise InvalidCredentialsError()
        else:
            return AuthenticatorServiceException(
                f"{response.status} f{response.read()}: "
            )

    def login(self, username: str, password: str):
        body = {"username": username, "password": password}
        response = self.call_authenticator("POST", "/login", body)

        return self.generateCookie(username)

    def validate(self, cookie: str) -> bool:
        try:
            cookie_content = jwt.decode(
                cookie, self.config.secret_key, algorithms=["HS256"]
            )
            body = {"username": cookie_content["username"]}
        except:
            raise InvalidCredentialsError("Cookie invalid or missing")

        response = self.call_authenticator("POST", "/usr", body)

        return True
