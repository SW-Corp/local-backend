import json
from dataclasses import dataclass, field
from typing import Dict, List

from pydantic import BaseModel

from .task_models import TaskNotification
from .auth import AuthController, PermissionType


class WebsocketConnectModel(BaseModel):
    workstation: str
    cookie: str


class WebsocketError(BaseModel):
    type: str
    data: str


@dataclass
class WebsocketService:
    authController: AuthController
    workstations: List[str] = field(default_factory=list)
    websockets: Dict[str, List] = field(default_factory=dict)

    def init_service(self, workstations):
        self.workstations = workstations
        for _workstation in self.workstations:
            self.websockets[_workstation] = []

    async def connect(self, websocket):
        try:
            added = False
            while True:
                connect_payload = json.loads(await websocket.receive_text())
                connect_model = WebsocketConnectModel(
                    workstation=connect_payload["workstation"],
                    cookie=connect_payload["cookie"],
                )
                if not added:
                    if connect_model.workstation not in self.workstations:
                        await websocket.send_text(
                            json.dumps(
                                WebsocketError(
                                    type="connectionerror", data="Invalid workstation!"
                                ).json()
                            )
                        )
                        websocket.close()
                        print("Error accepting socket, invalid workstation")
                        continue

                    if self.authController.config.mode == "ON" and not self.validate(
                        connect_model.cookie
                    ):
                        await websocket.send_text(
                            json.dumps(
                                WebsocketError(
                                    type="connectionerror", data="Not validated!"
                                ).json()
                            )
                        )
                        websocket.close()
                        print("Error accepting socket, not validated")
                        continue

                    self.websockets[str(connect_model.workstation)].append(websocket)
                    added = True
        except Exception as e:
            await websocket.send_text(
                json.dumps(
                    WebsocketError(
                        type="connectionerror", data=f"Error accepting socket connection: {e}"
                    ).json()
                )
            )
            print(f"Error accepting socket connection: {e}")

    def validate(self, cookie: str):
        pass
        # return self.authController.validate(cookie, PermissionType.READ)


class NotificationsService(WebsocketService):
    async def broadcast_notification(
        self, workstation: str, notification: TaskNotification
    ):
        for websocket in self.websockets[workstation]:
            try:
                await websocket.send_text(json.dumps(notification.json()))
            except Exception as e:
                print(f"error sending to socket {e}")


class PushingStateService(WebsocketService):
    async def broadcast_state(self, workstation: str, state: BaseModel):
        print(self.websockets[workstation])
        for websocket in self.websockets[workstation]:
            try:
                await websocket.send_text(json.dumps(state.json()))
            except Exception as e:
                print(f"error sending to socket {e}")
