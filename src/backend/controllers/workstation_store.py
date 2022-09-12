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
    component: Component
    metric: MetricType

class WorkstationSpecification(BaseModel):
    info: WorkstationInfo
    components: List[Component]
    metrics: List[ComponentMetric]
