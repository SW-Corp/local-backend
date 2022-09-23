import json
from dataclasses import dataclass, field
from typing import Dict, List

from pydantic import BaseModel

from ..controllers.task_models import TaskNotification


@dataclass
class WebsocketService:
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
                workstation = await websocket.receive_text()
                if not added:
                    if workstation not in self.workstations:
                        await websocket.send_text("Invalid workstation!")
                        continue

                    self.websockets[str(workstation)].append(websocket)
                    added = True
                    await websocket.send_text("Connected")
        except Exception:
            pass


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
        for websocket in self.websockets[workstation]:
            try:
                await websocket.send_text(json.dumps(state.json()))
            except Exception as e:
                print(f"error sending to socket {e}")
