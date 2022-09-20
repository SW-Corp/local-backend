import json
from dataclasses import dataclass, field
from typing import Dict, List

from backend.exceptions import workstation

from ..controllers.task_models import TaskNotification


@dataclass
class NotificationsService:
    workstations: List[str] = field(default_factory=list)
    websockets: Dict[str, List] = field(default_factory=dict)

    def init_service(self, workstations):
        self.workstations = workstations
        for _workstation in self.workstations:
            self.websockets[_workstation] = []

    async def broadcast_notification(
        self, workstation: workstation, notification: TaskNotification
    ):
        for websocket in self.websockets[workstation]:
            try:
                await websocket.send_text(json.dumps(notification.json()))
            except Exception as e:
                print(f"error sending to socket {e}")

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
