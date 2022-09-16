from enum import Enum
from pydantic import BaseModel
from typing import Optional, List

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
    ttl: Optional[int]
    conditions: Conditions
