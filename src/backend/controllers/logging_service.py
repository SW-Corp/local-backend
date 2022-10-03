from dataclasses import dataclass

from dataclasses import dataclass
from queue import Queue
from typing import Tuple
import time

@dataclass
class Logger():
    queue: Queue[Tuple[float, str]]= Queue(maxsize=1000)

    def log(self, message):
        if message:
            self.queue.put({"timestamp": time.time(), "log": message})

    def getLoggingHistory(self):
        return list(reversed(list(self.queue.queue)))