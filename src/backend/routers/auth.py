from typing import Union

from fastapi import APIRouter, Cookie, Response
from pydantic import BaseModel

from ..controllers import AuthController


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
        async def signup():
            pass

        @router.post("/login", response_model=LoginResponse)
        async def login(
            loginData: LoginBody,
            response: Response,
            Authorization: Union[str, None] = Cookie(default=None),
        ):
            print(Authorization)
            cookie = self.authController.login(loginData.email, loginData.password)
            response.headers["Set-Cookie"] = cookie
            return LoginResponse(email=loginData.email, message="login")

        @router.get("/logout")
        async def logout(response: Response):
            response.set_cookie("Authorization", "", 0)
            return "logout"

        return router
