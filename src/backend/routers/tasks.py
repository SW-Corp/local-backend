from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from ..controllers import Task, TasksController
from ..controllers.scenario_parser import ScenarioParser
from ..exceptions import WorkstationNotFound


class TasksRouterBuilder:
    def __init__(self, tasksController: TasksController):
        self.tasksController: TasksController = tasksController
        self.scenarioParser: ScenarioParser = ScenarioParser()

    def build(self) -> APIRouter:
        router = APIRouter()

        @router.get("/task/list/{workstation}", response_model=List[Task])
        async def listTasks(workstation: str):
            try:
                return self.tasksController.getQueue(workstation)
            except WorkstationNotFound:
                raise HTTPException(404, "Workstation not found")

        @router.post("/task/flush/{workstation}")
        async def clearTasks(workstation: str):
            try:
                self.tasksController.flushQueue(workstation)
            except WorkstationNotFound:
                raise HTTPException(404, "Workstation not found")

        @router.post("/task/{workstation}")
        async def addTask(workstation: str, task: Task):
            try:
                self.tasksController.addTask(workstation, task)
            except WorkstationNotFound:
                raise HTTPException(404, "Workstation not found")
            return JSONResponse(content="Added task to the queue!")

        @router.post("/scenario/{workstation}/{scenario_name}")
        async def playScenario(workstation: str, scenario_name: str):
            scenario: List[Task] = self.scenarioParser.parse_from_json_file(
                f"./src/backend/assets/scenarios/{scenario_name}"
            )
            for task in scenario:
                self.tasksController.addTask(workstation, task)

        return router
