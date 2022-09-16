from enum import Enum
from pydantic import BaseModel
from typing import Dict, List


class MetricType(str, Enum):
    WATER_LEVEL = "water_level"
    OPEN_LEVEL = "open_level"


class ComponentType(str, Enum):
    VALVE = "valve"
    PUMP = "pump"
    TANK = "tank"


class WorkstationInfo(BaseModel):
    name: str
    description: str
    connector_address: str
    connector_port: int


class Component(BaseModel):
    component_id: int
    name: str
    readable_name: str
    component_type: ComponentType


class ComponentMetric(BaseModel):
    component_id: str
    metric: MetricType


class WorkstationSpecification(BaseModel):
    info: WorkstationInfo
    components: List[Component]
    metrics: List[ComponentMetric]

def init_store(dbService):
    store = {}
    worstations_query = "SELECT * FROM WORKSTATIONS"
    components_query = "SELECT * FROM COMPONENTS"
    metrics_query = "SELECT * FROM COMPONENTS INNER JOIN METRICS on COMPONENTS.component_type = METRICS.component_type;"

    workstations_response = dbService.run_query(worstations_query)
    components_response = dbService.run_query(components_query)
    metrics_response = dbService.run_query(metrics_query)

    workstation_names = list(map(lambda x: x["name"], workstations_response))
    

    for workstation_name in workstation_names:
        metrics: List[ComponentMetric] = []
        components: List[Component] = []
        workstation_record = list(filter(
            lambda x: x["name"] == workstation_name, workstations_response
        ))[0]
        component_records = list(filter(
            lambda x: x["workstation"] == workstation_name, components_response
        ))
        metrics_records = list(filter(
            lambda x: x["workstation"] == workstation_name, metrics_response
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
                    component_id=metric["component_id"],
                    metric=MetricType(metric["metric_type"]),
                )
            )

        store[workstation_name] = WorkstationSpecification(
            info=workstation_info, components=components, metrics=metrics
        )

    return store    