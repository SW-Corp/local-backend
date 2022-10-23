import json
from asyncio.log import logger
from dataclasses import dataclass
from typing import List, Tuple
from ..exceptions.task import ErrorParsingTask
from .task_models import Condition, Conditions, ConditionType, Operator, Task
import traceback

class InvalidValue(Exception):
    def __init__(self, field, value, allowed):
        self.field = field
        self.value = value
        self.allowed = allowed
        self.message = f"'{value}' is invalid value of '{field}'. Allowed: {allowed}"
        super().__init__(self.message)

measurements = [
    'current',
    'voltage',
    'water_level',
    'is_on',
    'is_open',
    'float_switch_up',
    'pressure']

types = [
    'equal',
    'more',
    'less',
    'moreequal',
    'lessequal'
    ]

pumps = [f"P{i}" for i in range(1, 5)]
valves = [f"V{i}" for i in range(1, 4)]
containers = [f"C{i}" for i in range(1, 6)]

def validateFields(fields, data):
    allowed = {
        "target": pumps + valves,
        "type": types,
        "measurement": measurements,
        "field": pumps + valves + containers
    }
    for field in fields:
        if data[field] not in allowed[field]:
            raise InvalidValue(field, data[field], allowed[field])

@dataclass
class ScenarioParser:
    def parse_from_json_file(self, filename: str) -> Tuple[List[Task], Conditions]:
        with open(filename, "r") as file:
            try:
                data = json.load(file)
                return self.parse_from_json(data)
            except Exception as e:
                logger.error(f"Error parsing task {e}{traceback.format_exc()}")
                raise ErrorParsingTask
             

    def parse_from_json(self, data) -> Tuple[List[Task], Conditions]:
        initial_contitions: Conditions = self.getConditions(data.get("initial_conditions", None))

        taskList: List[Task] = []
        

        for task in data["tasks"]:
            conditions: Conditions = self.getConditions(task.get("conditions", None))
            validateFields(["target"], task)
            taskItem = Task(
                action=task["action"],
                target=task["target"],
                value=task["value"],
                timeout=task.get("timeout", None),
                ttl=task.get("ttl", None),
                drop_after_ttl=task.get("drop_after_ttl", False),
                conditions=conditions,
            )
            taskList.append(taskItem)
        return taskList, initial_contitions

    def getConditions(self, conditions) -> Conditions:
            conditionList: List[Condition] = []
            if not conditions:
                conditions = None
            else:
                for condition in conditions["conditionlist"]:
                    validateFields(["type", "measurement", "field"], condition)
                    conditionList.append(
                        Condition(
                            type=ConditionType(condition["type"]),
                            measurement=condition["measurement"],
                            field=condition["field"],
                            value=condition["value"],
                        )
                    )
                conditions = Conditions(
                    operator=Operator(conditions["operator"]),
                    conditionlist=conditionList,
                )
            
            return conditions