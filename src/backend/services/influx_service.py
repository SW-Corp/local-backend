from dataclasses import dataclass

from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from ..utils import get_logger

logger = get_logger("IFLUX")

HARDCODED_BUCKET = "YOUR-BUCKET"


@dataclass
class InfluxConfig:
    address: str
    port: int
    token: str
    org: str


@dataclass
class InfluxService:
    config: InfluxConfig

    def __post_init__(self):
        try:
            self.influxClient: InfluxDBClient = InfluxDBClient(
                url=f"http://{self.config.address}:{self.config.port}",
                token=self.config.token,
                org=self.config.org,
            )
        except Exception as e:
            logger.error(
                f"Error connecting to influx ({self.config.address}:{self.config.port}): {e}"
            )
            exit(1)

        self.write_api = self.influxClient.write_api(write_options=SYNCHRONOUS)
        self.query_api = self.influxClient.query_api()

    def write(self, workstation: str, metrics: list) -> None:
        points = []
        for i in metrics:
            points.append(
                Point(i.measurement)
                .tag("workstation", workstation)
                .field(i.field, i.value)
            )
        self.write_api.write(
            bucket=HARDCODED_BUCKET, org=self.config.org, record=points
        )

    def read(self, query):
        result = self.query_api.query(org=self.config.org, query=query)
        return result
