from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class Operator(str, Enum):
    AND = "and"
    OR = "or"


class ConditionType(str, Enum):
    EQUAL = "equal"
    LESS = "less"
    MORE = "more"
    MOREEQUAL = "moreequal"
    LESSEQUAL = "lessequal"


class TaskStatus(str, Enum):
    SUCCESS = "success"
    CONDITIONS_NOT_MET = "conditions_not_met"
    CONNECTOR_ERROR = "connector_error"


class Condition(BaseModel):
    type: ConditionType
    measurement: str
    field: str
    value: float


class Conditions(BaseModel):
    operator: Operator
    conditionlist: List[Condition]

class TaskAction(str, Enum):
    IS_ON = "is_on"
    IS_OPEN = "is_open"
    STOP = "stop"
    END_SCENARIO = "end_scenario" #internal use only


class Task(BaseModel):
    action: TaskAction
    target: str
    value: float
    ttl: Optional[int]
    timeout: Optional[int]
    conditions: Optional[Conditions]


class TaskNotification(BaseModel):
    status: TaskStatus
    task: Task
    type: str = "notification"
