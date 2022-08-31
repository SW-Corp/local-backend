from dataclasses import dataclass, field
from enum import Enum
from http.client import HTTPConnection
from queue import Queue
from typing import Dict, List
from threading import Thread

from pydantic import BaseModel

from backend.exceptions.workstation import WorkstationException

from ..exceptions import WorkstationNotFound
from .workstation import WorkstationController
from ..utils import get_logger

logger = get_logger("Tasks controller")

class Operator(str, Enum):
    AND = "and"
    OR = "or"


class ConditionType(str, Enum):
    TIMEOUT = "timeout"
    EQUAL = "equal"
    LESS = "less"
    MORE = "more"
    MOREEQUAL = "moreequal"
    LESSEQUAL = "lessequal"


class Condition(BaseModel):
    type: ConditionType
    measurement: str
    field: str
    value: float


class Conditions(BaseModel):
    operator: Operator
    conditionlist: List[Condition]

class Task(BaseModel):
    action: str
    target: str
    value: float
    conditions: Conditions

class WorkstationData(BaseModel):
    name: str
    test: str
    address: str
    port: int


def check_conditions(task: Task):
    #TODO checking conditions
    return True

def send_task(httpconnection: HTTPConnection, task: Task):
    # try:
    body = task.json()
    httpconnection.request("POST", "/task", body)
    response = httpconnection.getresponse()
    data = response.read()
    # except Exception as e:
    #     logger.debug(f"Error sending task {e}")
    #     return

    if response.status == 200:
        logger.debug("Successfully sent a task!")
    else:
        logger.debug("Error sending task")


def push_tasks_to_station(queue: Queue[Task], workstationData: WorkstationData):
    httpconnection: HTTPConnection = HTTPConnection(workstationData.address, workstationData.port)
    print(workstationData)
    while True:
        task: Task = queue.get()
        logger.debug("Got task from the queue")
        if not check_conditions(task):
            return
            #TODO waiting till conditions are met
        send_task(httpconnection, task)
        


@dataclass
class TasksController:
    workstationController: WorkstationController
    workstationsData: Dict[str, WorkstationData] = field(default_factory=dict)
    pushingThreads: Dict[str, Thread] = field(default_factory=dict)
    taskQueuesStore: Dict[str, Queue[Task]] = field(default_factory=dict)

    def __post_init__(self):
        workstations = self.workstationController.getWorkstations()
        for record in workstations:
            stationData: WorkstationData = WorkstationData(
                name=record["name"],
                test=record["test"],
                address=record["connector_address"],
                port=record["connector_port"],
            )
            queue = Queue(maxsize=20)
        
            thread = Thread(target=push_tasks_to_station, args=(queue, stationData))
            thread.start()

            self.taskQueuesStore[stationData.name] = queue
            self.workstationsData[stationData.name] = stationData
            self.pushingThreads[stationData.name] = thread


        print(self.taskQueuesStore, self.pushingThreads, self.workstationsData)

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
