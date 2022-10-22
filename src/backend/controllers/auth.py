import json
from dataclasses import dataclass
from enum import Enum
from http.client import HTTPConnection
from typing import List

import jwt
from pydantic import BaseModel

from backend.exceptions.auth import InsufficientPermission

from ..exceptions import AuthenticatorServiceException, InvalidCredentialsError
from ..services import DBService


class PermissionType(str, Enum):
    READ = "read"
    WRITE = "write"
    MANAGE_USERS = "manage_users"


class Permission(BaseModel):
    user: str
    permission: PermissionType


class UserList(BaseModel):
    users: List[Permission]


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
    dbService: DBService

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
            raise InvalidCredentialsError("Invalid credentials")
        if response.status == 403:
            raise InsufficientPermission("Insufficient permission")
        else:
            raise AuthenticatorServiceException(
                f"{response.status} {response.read().decode()}: "
            )

    def signup(self, username: str, password: str):
        try:
            body = {"username": username, "password": password}
            self.call_authenticator("POST", "/signup", body)

        except Exception as e:
            raise AuthenticatorServiceException(f"Error signing up: {e}")

    def login(self, username: str, password: str):
        body = {"username": username, "password": password}
        response = self.call_authenticator("POST", "/login", body)
        permission = json.loads(response)["permission"]
        return self.generateCookie(username), permission

    def get_user_from_cookie(self, cookie: str):
        try:
            cookie_content = jwt.decode(
                cookie, self.config.secret_key, algorithms=["HS256"]
            )
            return cookie_content["username"]
        except Exception:
            raise InvalidCredentialsError("Cookie invalid or missing")

    def validate(self, cookie: str, permission) -> bool:
        body = {"username": self.get_user_from_cookie(cookie), "permission": permission}

        self.call_authenticator("POST", "/permission", body)

        return True

    def add_permission(self, permission: Permission):
        # query = f"UPDATE USERS SET permission = '{permission.permission}' WHERE email = '{permission.user}'"
        query = f"UPDATE USERS SET permission = %s WHERE email = %s"
        self.dbService.run_query_insert(query, (permission.permission, permission.user, ))

    def delete_user(self, user: str):
        query = f"DELETE FROM USERS WHERE email = %s"
        self.dbService.run_query_insert(query, (user, ))

    def get_users(self) -> UserList:
        query = 'SELECT "email", "permission" FROM USERS'
        records = self.dbService.run_query(query)
        print("records")
        users = list(
            map(
                lambda x: Permission(
                    user=x["email"], permission=PermissionType(x["permission"])
                ),
                records,
            )
        )
        return UserList(users=users)
