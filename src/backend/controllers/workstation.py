from dataclasses import dataclass, field
from typing import Dict, List

from pydantic import BaseModel

from backend.exceptions import WorkstationNotFound
from backend.exceptions.workstation import InvalidMetric
from backend.services import DBService
from backend.services.influx_service import InfluxService
from backend.controllers.websockets_controller import (
    NotificationsService,
    PushingStateService,
)

from ..utils import get_logger
from .tasks import TasksController
from .workstation_store import (
    Component,
    ComponentType,
    MetricType,
    WorkstationInfo,
    WorkstationSpecification,
    init_store,
)

logger = get_logger("WORKSTATION_CONTROLLER")

HARDCODED_BUCKET = "WORKSTATION-DATA"


class MetricsData(BaseModel):
    measurement: str
    field: str
    value: float


class MetricsList(BaseModel):
    workstation_name: str
    metrics: List[MetricsData]


class MetricTypes(BaseModel):
    pass


class PumpState(BaseModel):
    voltage: float
    current: float
    is_on: bool


class ValveState(BaseModel):
    voltage: float
    current: float
    is_open: bool


class TankState(BaseModel):
    pressure: float
    offset: float
    water_level: float
    float_switch_up: bool
    water_volume: float


class WorkstationMetricsState(BaseModel):
    pumps: Dict[str, PumpState]
    valves: Dict[str, ValveState]
    tanks: Dict[str, TankState]
    currentScenario: str
    type: str = "state"


@dataclass
class WorkstationController:
    dbService: DBService
    influxService: InfluxService
    notificationService: NotificationsService
    pushingStateService: PushingStateService
    store: Dict[str, WorkstationSpecification] = field(
        default_factory=dict
    )  # read only
    tasksController = None  # crappy init TODO fix that

    def __post_init__(self):
        self.store = init_store(self.dbService)
        self.notificationService.init_service(list(self.store.keys()))
        self.pushingStateService.init_service(list(self.store.keys()))
        self.tasksController = TasksController(
            self.store, self.influxService, self.notificationService
        )

    def getStation(self, station_name: str) -> WorkstationInfo:
        try:
            return self.store[station_name]
        except Exception:
            raise WorkstationNotFound

    def getWorkstations(self) -> List[str]:
        return list(self.store.keys())

    def pullMetrics(self, station_name: str) -> MetricsData:
        try:
            return self.influxService.read(
                f'from(bucket:"{HARDCODED_BUCKET}") |> range(start: -10m)'
            )
        except Exception as e:
            logger.error(f"Error reading from influx: {e}")

    async def pushMetrics(self, metricList: MetricsList) -> None:
        components = self.store[metricList.workstation_name].components
        # I know, I know, don't repeat yourself
        pumps = list(
            filter(lambda x: x.component_type == ComponentType.PUMP, components)
        )
        tanks = list(
            filter(lambda x: x.component_type == ComponentType.TANK, components)
        )
        valves = list(
            filter(lambda x: x.component_type == ComponentType.VALVE, components)
        )

        pumps = list(map(lambda x: x.name, pumps))
        tanks = list(map(lambda x: x.name, tanks))
        valves = list(map(lambda x: x.name, valves))

        stateJson = {
            "pumps": {},
            "tanks": {},
            "valves": {},
        }

        for compnames, comptype in [
            (pumps, "pumps"),
            (tanks, "tanks"),
            (valves, "valves"),
        ]:
            for name in compnames:
                stateJson[comptype][name] = {}

        referencePressure: float = None
        workstationName: str = metricList.workstation_name
        currentScenario = self.tasksController.pushingThreads[workstationName].currentScenario
        workstationState: WorkstationMetricsState = WorkstationMetricsState(
            pumps={}, tanks={}, valves={}, currentScenario=currentScenario
        )

        try:
            for metric in metricList.metrics:
                comp_name = metric.field
                measurement = MetricType(metric.measurement)
                value = metric.value
                if comp_name == "reference" and measurement == "pressure":
                    referencePressure = value

                if comp_name in pumps:
                    stateJson["pumps"][comp_name][measurement] = value
                if comp_name in tanks:
                    stateJson["tanks"][comp_name][measurement] = value
                if comp_name in valves:
                    stateJson["valves"][comp_name][measurement] = value

            for pump in stateJson["pumps"]:
                voltage = stateJson["pumps"][pump][MetricType.VOLTAGE]
                current = stateJson["pumps"][pump][MetricType.CURRENT]
                pumpNumber = pump[1:]
                float_switch_up = stateJson["tanks"][f"C{pumpNumber}"][
                    MetricType.FLOAT_SWITCH_UP
                ]

                if voltage > 4 and current > 40 and not float_switch_up:
                    is_on = 1
                else:
                    is_on = 0
                workstationState.pumps[pump] = PumpState(
                    voltage=voltage, current=current, is_on=bool(is_on)
                )

                metricList.metrics.append(
                    MetricsData(
                        measurement=MetricType.IS_ON,
                        field=pump,
                        value=is_on,
                    )
                )

            for tank in stateJson["tanks"]:
                pressure = stateJson["tanks"][tank][MetricType.PRESSURE]
                float_switch_up = stateJson["tanks"][tank][MetricType.FLOAT_SWITCH_UP]
                tankComponent: Component = list(
                    filter(
                        lambda x: x.name == tank, self.store[workstationName].components
                    )
                )[0]
                offset= tankComponent.offset
                width = tankComponent.width
                lenght = tankComponent.length

                water_level = pressure - referencePressure - offset + 1
                workstationState.tanks[tank] = TankState(
                    pressure=pressure,
                    offset=offset,
                    water_level=water_level,
                    float_switch_up=float_switch_up,
                    water_volume = width*lenght*water_level
                )
                metricList.metrics.append(
                    MetricsData(
                        measurement=MetricType.WATER_LEVEL,
                        field=tank,
                        value=water_level,
                    )
                )

            for valve in stateJson["valves"]:
                current = stateJson["valves"][valve][MetricType.CURRENT]
                voltage = stateJson["valves"][valve][MetricType.VOLTAGE]

                if voltage > 4 and current > 40:
                    is_open = 1
                else:
                    is_open = 0

                workstationState.valves[valve] = ValveState(
                    current=current,
                    voltage=voltage,
                    is_open=bool(is_open),
                )

                metricList.metrics.append(
                    MetricsData(
                        measurement=MetricType.IS_OPEN,
                        field=valve,
                        value=is_open,
                    )
                )

                # if not self.validate_metric(metric, metricList.workstation_name):
                #     raise InvalidMetric(
                #         f"Metric {metric.field}, {metric.measurement} is invalid!"
                #     )
            self.influxService.write(
                workstation=metricList.workstation_name, metrics=metricList.metrics
            )

            
        except InvalidMetric as e:
            logger.debug(f"Invalid Metric {e}")

        except Exception as e:
            logger.error(f"Error writing to influx: {e}")
        await self.pushingStateService.broadcast_state(
            workstationName, workstationState
        )

    def validate_metric(self, metric: MetricsData, workstationName: str):
        def get_component_name(id):
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
