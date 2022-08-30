from dataclasses import dataclass
from enum import Enum
from queue import Queue
from typing import Dict, List

from pydantic import BaseModel

from backend.exceptions.workstation import WorkstationException

from ..exceptions import WorkstationNotFound
from .workstation import WorkstationController


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


@dataclass
class TasksController:
    workstationController: WorkstationController

    def __post_init__(self):
        self.taskQueuesStore: Dict[str, Queue[Task]] = {}
        workstations = self.workstationController.getWorkstationsNames()
        for i in workstations:
            self.taskQueuesStore[i["name"]] = Queue(maxsize=20)

        print(self.taskQueuesStore)

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
