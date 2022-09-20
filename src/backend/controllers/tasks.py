from dataclasses import dataclass, field
from queue import Queue
from threading import Thread
from typing import Dict, List

from pydantic import BaseModel

from backend.services.notifications_service import NotificationsService

from ..exceptions import WorkstationNotFound
from ..services import InfluxService
from ..utils import get_logger
from .task_models import Task
from .task_pusher import ClearQueueSignal, TaskPusherThread
from .workstation_store import WorkstationSpecification

logger = get_logger("Tasks controller")
HARDCODED_BUCKET = "YOUR-BUCKET"
DEFAULT_TASK_TIMEOUT = 10


class MetricsData(BaseModel):
    measurement: str
    field: str
    value: float


@dataclass
class TasksController:
    workstationsData: Dict[str, WorkstationSpecification]
    influx_service: InfluxService
    notificationsService: NotificationsService
    abort_task_signals: Dict[str, ClearQueueSignal] = field(default_factory=dict)
    pushingThreads: Dict[str, Thread] = field(default_factory=dict)
    taskQueuesStore: Dict[str, Queue[Task]] = field(default_factory=dict)

    def __post_init__(self):

        for station in self.workstationsData:

            queue = Queue(maxsize=20)
            self.abort_task_signals[station] = ClearQueueSignal()
            thread = TaskPusherThread(
                queue,
                self.workstationsData[station],
                self.influx_service,
                self.abort_task_signals[station],
                self.notificationsService,
            )
            thread.start()

            self.taskQueuesStore[station] = queue
            self.workstationsData[station] = self.workstationsData[station]
            self.pushingThreads[station] = thread

    def addTask(self, workstation: str, task: Task):
        try:
            self.taskQueuesStore[workstation].put(task)
        except KeyError:
            raise WorkstationNotFound

    def getQueue(self, workstation: str) -> List[Task]:
        try:
            return list(self.taskQueuesStore[workstation].queue)
        except KeyError:
            raise WorkstationNotFound

    def flushQueue(self, workstation: str):
        try:
            if self.pushingThreads[workstation].processing_task:
                with self.taskQueuesStore[workstation].mutex:
                    self.taskQueuesStore[workstation].queue.clear()
                self.abort_task_signals[workstation].toggle()
        except KeyError:
            raise WorkstationNotFound
