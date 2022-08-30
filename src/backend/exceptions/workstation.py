from dataclasses import dataclass


@dataclass
class WorkstationException(Exception):
    pass


class WorkstationNotFound(WorkstationException):
    pass
