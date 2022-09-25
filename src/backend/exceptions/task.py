class TaskException(Exception):
    pass


class ErrorParsingTask(TaskException):
    pass

class InvalidScenarioName(TaskException):
    pass

class InvalidScenarioFormat(TaskException):
    pass