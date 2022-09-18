from dataclasses import dataclass


@dataclass
class WorkstationException(Exception):
    pass


class WorkstationNotFound(WorkstationException):
    pass


@dataclass
class InvalidMetric(Exception):
    detail: str
