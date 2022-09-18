from dataclasses import dataclass, field
from typing import Dict, List

from pydantic import BaseModel

from backend.exceptions import WorkstationNotFound
from backend.exceptions.workstation import InvalidMetric
from backend.services import DBService
from backend.services.influx_service import InfluxService

from ..utils import get_logger
from .tasks import TasksController
from .workstation_store import (Component, WorkstationInfo,
                                WorkstationSpecification, init_store)

logger = get_logger("WORKSTATION_CONTROLLER")

HARDCODED_BUCKET = "YOUR-BUCKET"


class MetricsData(BaseModel):
    measurement: str
    field: str
    value: float


class MetricsList(BaseModel):
    workstation_name: str
    metrics: List[MetricsData]


class MetricTypes(BaseModel):
    pass


@dataclass
class WorkstationController:
    dbService: DBService
    influxService: InfluxService
    store: Dict[str, WorkstationSpecification] = field(
        default_factory=dict
    )  # read only
    tasksController = None  # crappy init TODO fix that

    def __post_init__(self):
        self.store = init_store(self.dbService)
        self.tasksController = TasksController(self.store, self.influxService)

    def getStation(self, station_name: str) -> WorkstationInfo:
        try:
            return self.store[station_name]
        except Exception:
            raise WorkstationNotFound

    def getWorkstations(self) -> List[str]:
        response = self.dbService.run_query(f"SELECT * FROM WORKSTATIONS")
        if not response:
            raise WorkstationNotFound

        return response

    def pullMetrics(self, station_name: str) -> MetricsData:
        try:
            return self.influxService.read(
                f'from(bucket:"{HARDCODED_BUCKET}") |> range(start: -10m)'
            )
        except Exception as e:
            logger.error(f"Error reading from influx: {e}")

    def pushMetrics(self, metricList: MetricsList) -> None:
        try:
            for metric in metricList.metrics:
                if not self.validate_metric(metric, metricList.workstation_name):
                    raise InvalidMetric(
                        f"Metric {metric.field}, {metric.measurement} is invalid!"
                    )
            self.influxService.write(
                workstation=metricList.workstation_name, metrics=metricList.metrics
            )
        except InvalidMetric as e:
            logger.debug(f"Invalid Metric {e}")

        except Exception as e:
            logger.error(f"Error writing to influx: {e}")

    def validate_metric(self, metric: MetricsData, workstationName: str):
        def get_component_name(id):
            component = list(
                filter(
                    lambda x: x.component_id == id,
                    self.store[workstationName].components,
                )
            )
            return list(
                filter(
                    lambda x: x.component_id == id,
                    self.store[workstationName].components,
                )
            )[0].name

        return (metric.field, metric.measurement) in list(
            map(
                lambda x: (get_component_name(x.component_id), x.metric),
                self.store[workstationName].metrics,
            )
        )
