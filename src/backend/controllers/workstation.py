from dataclasses import dataclass
from typing import List

from pydantic import BaseModel

from backend.exceptions import WorkstationNotFound
from backend.services import DBService
from backend.services.influx_service import InfluxService

from ..utils import get_logger

logger = get_logger("WORKSTATION_CONTROLLER")

HARDCODED_BUCKET = "YOUR-BUCKET"


class WorkstationInfo(BaseModel):
    name: str
    test: str

class MetricsData(BaseModel):
    measurement: str
    field: str
    value: float

class MetricsList(BaseModel):
    workstation_name: str
    metrics: List[MetricsData]

@dataclass
class WorkstationController:
    dbService: DBService
    influxService: InfluxService

    def getStation(self, station_name: str) -> WorkstationInfo:
        response = self.dbService.run_query(
            f"SELECT name, test FROM WORKSTATIONS WHERE name='{station_name}'"
        )
        if not response:
            raise WorkstationNotFound
        record = response[0]
        return WorkstationInfo(name=record["name"], test=record["test"])

    def pullMetrics(self, station_name: str) -> MetricsData:
        try:
            return self.influxService.read(
                f'from(bucket:"{HARDCODED_BUCKET}") |> range(start: -10m)'
            )
        except Exception as e:
            logger.error(f"Error reading from influx: {e}")

    def pushMetrics(self, metricList: MetricsList) -> None:
        try:
            self.influxService.write(workstation=metricList.workstation_name, metrics=metricList.metrics)
        except Exception as e:
            logger.error(f"Error writing to influx: {e}")
