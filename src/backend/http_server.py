from dataclasses import dataclass
from typing import Tuple
from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response

from backend.controllers.auth import PermissionType
from backend.exceptions.auth import InsufficientPermission

from .controllers import (
    AuthConfig,
    AuthController,
    WorkstationController,
    NotificationsService,
    PushingStateService,
)
from .exceptions import AuthenticatorServiceException, InvalidCredentialsError
from .routers import AuthRouterBuilder, TasksRouterBuilder, WorkstationRouterBuilder
from .services import DBConfig, DBService, InfluxConfig, InfluxService
from .controllers.logging_service import Logger

NOT_SECURED_PATHS = [
    ("/login", "POST"),
    ("/signup", "POST"),
]

# base permission
READ_PATHS = [
    ("/workstations", "GET"),
    ("/workstation", "GET"),
    ("/tasklist", "GET"),
    ("/metrics", "GET"),
    ("/logout", "GET"),
    ("/scenarios", "GET"),
    ("/logs", "GET")
]

WRITE_PATHS = [
    ("/flushqueue", "POST"),
    ("/task", "POST"),
    ("/scenario", "POST"),
    ("/metrics", "POST"),
    ("/scenario", "DELETE"),
    ("/addscenario", "POST"),
]

MANAGING_USERS_PATHS = [
    ("/users", "GET"),
    ("/user", "DELETE"),
    ("/permission", "POST"),
    ("/shutdown", "POST"),
    ("/calibrate", "POST")
]

AUTH_SCHEME = {
    PermissionType.READ: READ_PATHS,
    PermissionType.WRITE: WRITE_PATHS,
    PermissionType.MANAGE_USERS: MANAGING_USERS_PATHS,
}


def get_permission(path: Tuple[str, str]) -> PermissionType:
    for key in AUTH_SCHEME:
        if path in AUTH_SCHEME[key]:
            return key


@dataclass
class HTTPServer:
    authconfig: AuthConfig
    dbconfig: DBConfig
    influxconfig: InfluxConfig

    def build_app(self) -> FastAPI:  # noqa: C901
        app = FastAPI(title="HTTP keyserver", version="0.1")
        dbservice: DBService = DBService(self.dbconfig)
        loggingService: Logger = Logger
        influx_service: InfluxService = InfluxService(self.influxconfig)
        authController: AuthController = AuthController(self.authconfig, dbservice)
        notificationsService: NotificationsService = NotificationsService(
            authController
        )
        pushingStateService: PushingStateService = PushingStateService(authController)
        workstationController: WorkstationController = WorkstationController(
            dbservice, influx_service, notificationsService, pushingStateService, loggingService
        )

        @app.middleware("http")
        async def authMiddleware(request: Request, call_next):
            path = (f"/{request.scope['path'].split('/')[1]}", request.scope["method"])
            if path in NOT_SECURED_PATHS or self.authconfig.mode == "OFF":
                response = await call_next(request)
                return response
            else:
                permission: PermissionType = get_permission(path)
                try:
                    cookie = request.cookies["Authorization"]
                except Exception:
                    print("no cookie")
                    return JSONResponse("Authorization cookie missing", 401)
                try:
                    if authController.validate(cookie, permission):
                        user = authController.get_user_from_cookie(cookie)
                        request.state.request_user = user
                        response = await call_next(request)
                    else:
                        JSONResponse("Wrong email or password", 401)
                except InvalidCredentialsError as e:
                    return JSONResponse(e.detail, 401)
                except AuthenticatorServiceException as e:
                    return JSONResponse(e.detail, 500)
                except InsufficientPermission as e:
                    return JSONResponse(e.detail, 403)

            return response

        routers = {
            AuthRouterBuilder(authController),
            WorkstationRouterBuilder(workstationController),
            TasksRouterBuilder(workstationController.tasksController),
        }

        for router in routers:
            app.include_router(router.build())

        @app.websocket("/subscribe/notifications")
        async def handle_websocket_notification(websocket: WebSocket):
            await websocket.accept()
            await notificationsService.connect(websocket)

        @app.websocket("/subscribe/state")
        async def handle_websocket_state(websocket: WebSocket):
            await websocket.accept()
            await pushingStateService.connect(websocket)

        app.add_middleware(
            CORSMiddleware,
            allow_origins=[
                "http://localhost", "http://localhost:3000", "localhost", "localhost:3000", "control.lab", "http://control.lab",
                "http://10.8.0.9", "http://10.8.0.9:3000", "home.io", "http://home.io", "10.0.0.1", "http://10.0.0.1"
            ],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app
