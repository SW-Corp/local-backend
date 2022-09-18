from dataclasses import dataclass, field

from http.client import HTTPConnection
from queue import Queue
import time
from typing import Dict, List, Tuple
from threading import Thread
from ..services import InfluxService
from pydantic import BaseModel
from .workstation_store import WorkstationSpecification

from ..exceptions import WorkstationNotFound
from ..utils import get_logger

from .task_models import (
    Task, Operator, Condition, ConditionType
)

compare_func = {
    ConditionType.EQUAL: lambda x, y: x==y,
    ConditionType.LESS: lambda x, y: x<y,
    ConditionType.MORE: lambda x, y: x>y,
    ConditionType.MOREEQUAL: lambda x, y: x>=y,
    ConditionType.LESSEQUAL: lambda x, y: x<=y,
}

logger = get_logger("Tasks controller")
HARDCODED_BUCKET = "YOUR-BUCKET"
DEFAULT_TASK_TIMEOUT = 10

class MetricsData(BaseModel):
    measurement: str
    field: str
    value: float

def send_task(httpconnection: HTTPConnection, task: Task):
    try:
        body = task.json()
        httpconnection.request("POST", "/task", body)
        response = httpconnection.getresponse()
        data = response.read()
    except Exception as e:
        logger.debug(f"Error sending task {e}")
        raise Exception
        return

    if response.status == 200:
        logger.debug("Successfully sent a task!")
    else:
        logger.debug(f"Error sending task: {response}")
        raise Exception

def fluxtable_to_metrics_data(fluxtable: list) -> Dict[Tuple[str, str], float]:
    metrics: Dict[str, float] = {}
    for metric in fluxtable:
        record = metric.records[0]
        metrics[(record.get_measurement(), record.get_field())] = record.get_value()
    return metrics

def compare_metrics_and_conditions(op: Operator, conditions: List[Condition], metric_dict: Dict[Tuple[str, str], float]):
        if op == Operator.OR:
            conditions_met = False
            for condition in conditions:
                # ignoring timeout conditions, they are handled earlier
                if condition.type == ConditionType.TIMEOUT:
                    continue
                expected_value = condition.value
                metric_value = metric_dict[(condition.measurement, condition.field)]
                if compare_func[condition.type](metric_value, expected_value):
                    return True
            return False

        if op == Operator.AND:
            for condition in conditions:
                if condition.type == ConditionType.TIMEOUT:
                    continue

                expected_value = condition.value
                metric_value = metric_dict[(condition.measurement, condition.field)]
                if not compare_func[condition.type](metric_value, expected_value):
                    return False
            return True

def push_tasks_to_station(queue: Queue[Task], workstationData: WorkstationSpecification, influx_service: InfluxService):
    def getConditionsMetrics(conditions: List[Condition]):
        query_conditions: List[str] = map(lambda x: f' (r._measurement == "{x.measurement}" and r._field == "{x.field}") ', conditions)
        query = f'from(bucket:"{HARDCODED_BUCKET}") \
            |> range(start: -10s) \
            |> tail(n: 1)\
            |> filter(fn: (r) => {"or".join(query_conditions)}) \
            '
        try:
            return influx_service.read(query)
        except Exception as e:
            logger.error(f"Error reading from influx: {e}")

    def check_conditions(task: Task):
        beginning = time.time()
        if not task.conditions:
            return True
        op: Operator = task.conditions.operator
        conditions: List[Condition] = task.conditions.conditionlist
        timeoutCondition = list(filter(lambda x: x.type == ConditionType.TIMEOUT, conditions))

        if task.ttl:
            timeout = beginning + task.ttl
        else:
            timeout = beginning + DEFAULT_TASK_TIMEOUT

        if timeoutCondition:
            time.sleep(timeoutCondition[0].value)
            #TODO handle when ttl is longer than timeout

        while time.time() <= timeout:
            conditions_metrics = getConditionsMetrics(task.conditions.conditionlist)
            logger.info(f"got metrics {conditions_metrics}")
            metric_dict: Dict[Tuple[str, str], float] = fluxtable_to_metrics_data(conditions_metrics) # (measurement: vield): value
            try:
                if compare_metrics_and_conditions(task.conditions.operator, conditions, metric_dict):
                    return True
            except KeyError as e:
                logger.error("Task condition is invalid, metric doesn't exist")
                return False
            time.sleep(1)

        return False
        


    httpconnection: HTTPConnection = HTTPConnection(
        workstationData.info.connector_address, workstationData.info.connector_port
    )
    while True:
        task: Task = queue.get()
        logger.debug("Got task from the queue")
        if not check_conditions(task):
            logger.debug("contitions not met")
            continue
    
        try:
            send_task(httpconnection, task)
        except:
            time.sleep(1)
            logger.info("Trying to reconnect to connector")
            httpconnection = HTTPConnection(
            workstationData.info.connector_address, workstationData.info.connector_port
            )

@dataclass
class TasksController:
    workstationsData: Dict[str, WorkstationSpecification]
    influx_service: InfluxService
    pushingThreads: Dict[str, Thread] = field(default_factory=dict)
    taskQueuesStore: Dict[str, Queue[Task]] = field(default_factory=dict)

    def __post_init__(self):

        for station in self.workstationsData:

            queue = Queue(maxsize=20)

            thread = Thread(
                target=push_tasks_to_station,
                args=(queue, self.workstationsData[station], self.influx_service),
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
