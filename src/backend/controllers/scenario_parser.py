import json
from dataclasses import dataclass
from typing import List

from ..exceptions.task import ErrorParsingTask
from .task_models import Condition, Conditions, ConditionType, Operator, Task
import os


@dataclass
class ScenarioParser:
    def parse_from_json_file(self, filename: str) -> List[Task]:
        with open(filename, "r") as file:
            try:
                data = json.load(file)
                return self.parse_from_json(data["tasks"])
            except KeyError as e:
                raise ErrorParsingTask

    def parse_from_json(self, data: list) -> List[Task]:
        taskList: List[Task] = []
        for task in data:
            conditionList: List[Condition] = []
            for condition in task["conditions"]["conditionlist"]:
                conditionList.append(
                    Condition(
                        type=ConditionType(condition["type"]),
                        measurement=condition["measurement"],
                        field=condition["field"],
                        value=condition["value"],
                    )
                )
            conditions = Conditions(
                operator=Operator(task["conditions"]["operator"]),
                conditionlist=conditionList,
            )
            taskItem = Task(
                action=task["action"],
                target=task["target"],
                value=task["value"],
                conditions=conditions,
            )
            taskList.append(taskItem)
        return taskList
