from dataclasses import dataclass, field
from typing import List, Dict

from pydantic import BaseModel

from backend.exceptions import WorkstationNotFound
from backend.services import DBService
from backend.services.influx_service import InfluxService

from ..utils import get_logger
from .tasks import TasksController
from .workstation_store import (
    MetricType,
    WorkstationSpecification,
    WorkstationInfo,
    Component,
    ComponentMetric,
    ComponentType,
)

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
    tasksController = None # crappy init TODO fix that  
    def __post_init__(self):
        print("workstation post init")
        worstations_query = "SELECT * FROM WORKSTATIONS"
        components_query = "SELECT * FROM COMPONENTS"
        metrics_query = "SELECT * FROM COMPONENTS INNER JOIN METRICS on COMPONENTS.component_type = METRICS.component_type;"

        workstations_response = self.dbService.run_query(worstations_query)
        components_response = self.dbService.run_query(components_query)
        metrics_response = self.dbService.run_query(metrics_query)

        workstation_names = list(map(lambda x: x["name"], workstations_response))
        

        for workstation_name in workstation_names:
            metrics: List[ComponentMetric] = []
            components: List[Component] = []
            workstation_record = list(filter(
                lambda x: x["name"] == workstation_name, workstations_response
            ))[0]
            component_records = list(filter(
                lambda x: x["name"] == workstation_name, components_response
            ))
            metrics_records = list(filter(
                lambda x: x["name"] == workstation_name, metrics_response
            ))

            workstation_info: WorkstationInfo = WorkstationInfo(
                name=workstation_record["name"],
                description=workstation_record["description"],
                connector_address=workstation_record["connector_address"],
                connector_port=workstation_record["connector_port"],
            )

            for component in component_records:
                components.append(
                    Component(
                        component_id=component["component_id"],
                        name=component["name"],
                        readable_name=component["readable_name"],
                        component_type=ComponentType(component["component_type"]),
                    )
                )
            # component is stored in metrics and in components idk its kinda sloppy but its easier thiw way xd
            for metric in metrics_records:
                metrics.append(
                    ComponentMetric(
                        component=Component(
                            component_id=metric["component_id"],
                            name=metric["name"],
                            readable_name=metric["readable_name"],
                            component_type=ComponentType(metric["component_type"]),
                        ),
                        metric=MetricType(metric["type"]),
                    )
                )

            self.store[workstation_name] = WorkstationSpecification(
                info=workstation_info, components=components, metrics=metrics
            )
        self.tasksController = TasksController(self.store)

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
            self.influxService.write(
                workstation=metricList.workstation_name, metrics=metricList.metrics
            )
        except Exception as e:
            logger.error(f"Error writing to influx: {e}")

    def listComponents(self, workstation: str) -> List[Component]:
        pass

    def listMertics(self, workstation: str) -> MetricsList:
        pass
