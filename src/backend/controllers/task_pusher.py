import asyncio
import time
from dataclasses import dataclass
from http.client import HTTPConnection
from queue import Queue
from threading import Thread
from typing import Dict, List, Tuple

from backend.controllers.websockets_controller import NotificationsService

from ..services import InfluxService
from ..utils import get_logger
from .task_models import (
    Condition,
    ConditionType,
    Operator,
    Task,
    TaskNotification,
    TaskStatus,
)
from .workstation_store import WorkstationSpecification

logger = get_logger("Task pusher")

HARDCODED_BUCKET = "YOUR-BUCKET"
DEFAULT_TASK_TIMEOUT = 10

compare_func = {
    ConditionType.EQUAL: lambda x, y: x == y,
    ConditionType.LESS: lambda x, y: x < y,
    ConditionType.MORE: lambda x, y: x > y,
    ConditionType.MOREEQUAL: lambda x, y: x >= y,
    ConditionType.LESSEQUAL: lambda x, y: x <= y,
}


# custom variable used for clearing queue and aborting currnent task
@dataclass
class ClearQueueSignal:
    value: bool = False
    timestamp: float = 0
    ttl: int = 10

    def get_value(self):
        temp = self.value
        if self.value:
            self.value = False
            print(time.time(), self.timestamp, self.ttl)
            if time.time() > self.timestamp + self.ttl:
                logger.debug("flush orderd expired")
                return False

        return temp

    def toggle(self):
        self.timestamp = time.time()
        self.value = True


class TaskPusherThread(Thread):
    def __init__(
        self, queue, workstationData, influx_service, abort_task, notificationsService
    ):
        super(TaskPusherThread, self).__init__()
        self.queue: Queue[Task] = queue
        self.workstationData: WorkstationSpecification = workstationData
        self.influx_service: InfluxService = influx_service
        self.abort_task: ClearQueueSignal = abort_task
        self.notificationsService: NotificationsService = notificationsService
        self.processing_task: bool = False
        self.loop = asyncio.new_event_loop()

    def sendNotification(self, status: TaskStatus, task: Task):
        self.loop.run_until_complete(
            self.notificationsService.broadcast_notification(
                self.workstationData.info.name,
                TaskNotification(status=TaskStatus(status), task=task),
            )
        )

    def run(self):
        httpconnection: HTTPConnection = HTTPConnection(
            self.workstationData.info.connector_address,
            self.workstationData.info.connector_port,
        )
        while True:
            task: Task = self.queue.get()
            self.processing_task = True
            logger.debug("Got task from the queue")
            if not self.check_conditions(task):
                self.sendNotification(TaskStatus.CONDITIONS_NOT_MET, task)
                logger.debug("contitions not met")
                continue

            try:
                self.processing_task = False
                self.send_task(httpconnection, task)
                self.sendNotification(TaskStatus.SUCCESS, task)
            except Exception:
                self.sendNotification(TaskStatus.CONNECTOR_ERROR, task)
                time.sleep(1)
                logger.info("Trying to reconnect to connector")
                httpconnection = HTTPConnection(
                    self.workstationData.info.connector_address,
                    self.workstationData.info.connector_port,
                )

    def getConditionsMetrics(self, conditions: List[Condition]):
        query_conditions: List[str] = map(
            lambda x: f' (r._measurement == "{x.measurement}" and r._field == "{x.field}") ',
            conditions,
        )
        query = f'from(bucket:"{HARDCODED_BUCKET}") \
            |> range(start: -10s) \
            |> tail(n: 1)\
            |> filter(fn: (r) => {"or".join(query_conditions)}) \
            '
        try:
            return self.influx_service.read(query)
        except Exception as e:
            logger.error(f"Error reading from influx: {e}")

    def compare_metrics_and_conditions(
        self,
        op: Operator,
        conditions: List[Condition],
        metric_dict: Dict[Tuple[str, str], float],
    ):
        if op == Operator.OR:
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

    def check_conditions(self, task: Task):
        beginning = time.time()
        if not task.conditions:
            return True
        conditions: List[Condition] = task.conditions.conditionlist
        timeoutCondition = list(
            filter(lambda x: x.type == ConditionType.TIMEOUT, conditions)
        )

        if task.ttl:
            timeout = beginning + task.ttl
        else:
            timeout = beginning + DEFAULT_TASK_TIMEOUT

        if timeoutCondition:
            timeout += timeoutCondition[0].value
            while time.time() <= beginning + timeoutCondition[0].value:
                time.sleep(0.5)
                logger.debug("timeout...")
                if self.abort_task.get_value():
                    logger.debug("flush order")
                    return False

        while time.time() <= timeout:
            if self.abort_task.get_value():
                return False
            conditions_metrics = self.getConditionsMetrics(
                task.conditions.conditionlist
            )
            logger.info(f"got metrics {conditions_metrics}")
            metric_dict: Dict[Tuple[str, str], float] = self.fluxtable_to_metrics_data(
                conditions_metrics
            )  # (measurement: vield): value
            try:
                if self.compare_metrics_and_conditions(
                    task.conditions.operator, conditions, metric_dict
                ):
                    return True
            except KeyError as e:
                logger.error(f"Task condition is invalid, metric doesn't exist {e}")
                return False
            time.sleep(1)

        return False

    def send_task(self, httpconnection: HTTPConnection, task: Task):
        try:
            body = task.json()
            httpconnection.request("POST", "/task", body)
            response = httpconnection.getresponse()
            response.read()
        except Exception as e:
            logger.debug(f"Error sending task {e}")
            raise Exception

        if response.status == 200:
            logger.debug("Successfully sent a task!")
        else:
            logger.debug(f"Error sending task: {response}")
            raise Exception

    def fluxtable_to_metrics_data(
        self, fluxtable: list
    ) -> Dict[Tuple[str, str], float]:
        metrics: Dict[str, float] = {}
        for metric in fluxtable:
            record = metric.records[0]
            metrics[(record.get_measurement(), record.get_field())] = record.get_value()
        return metrics
