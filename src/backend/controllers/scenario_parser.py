import json
from asyncio.log import logger
from dataclasses import dataclass
from typing import List, Tuple
from ..exceptions.task import ErrorParsingTask
from .task_models import Condition, Conditions, ConditionType, Operator, Task
import traceback

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
            taskItem = Task(
                action=task["action"],
                target=task["target"],
                value=task["value"],
                timeout=task.get("timeout", None),
                ttl=task.get("ttl", None),
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