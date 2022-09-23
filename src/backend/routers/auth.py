from typing import Union

from fastapi import APIRouter, Cookie, HTTPException, Response, Request
from pydantic import BaseModel

from backend.controllers.auth import Permission, UserList
from backend.exceptions.auth import InvalidCredentialsError

from ..controllers import AuthController


class User(BaseModel):
    email: str

class LoginBody(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    email: str
    message: str


class AuthRouterBuilder:
    def __init__(self, authController: AuthController):
        self.authController: AuthController = authController

    def build(self) -> APIRouter:
        router = APIRouter()

        @router.post("/signup")
        async def signup(loginData: LoginBody):
            try:
                self.authController.signup(loginData.email, loginData.password)
            except Exception as e:
                return HTTPException(500, e)

        @router.post("/login", response_model=LoginResponse)
        async def login(
            loginData: LoginBody,
            response: Response,
            Authorization: Union[str, None] = Cookie(default=None),
        ):
            print(Authorization)
            try:
                cookie = self.authController.login(loginData.email, loginData.password)
                response.headers["Set-Cookie"] = cookie
            except InvalidCredentialsError:
                raise HTTPException(401, "Invalid credentials")

            return LoginResponse(email=loginData.email, message="login")

        @router.get("/logout")
        async def logout(response: Response):
            response.set_cookie("Authorization", "", 0)
            return "logout"

        @router.get("/users", response_model=UserList)
        async def get_users():
            return self.authController.get_users()

        @router.delete("/user")
        async def delete_user(user: User, request: Request):
            if request.state.request_user == user.email:
                raise HTTPException(404, "Can't delete yourself!")

            return self.authController.delete_user(user.email)

        @router.post("/permission")
        async def add_permission(permission: Permission, request: Request):
            if request.state.request_user == permission.user:
                raise HTTPException(404, "Can't edit your own permission!")

            try:
                self.authController.add_permission(permission)
            except Exception as e:
                raise HTTPException(500, str(e))

        return router
