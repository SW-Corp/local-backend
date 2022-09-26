from typing import List

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from backend.controllers import workstation
from backend.controllers.task_models import TaskAction

from ..controllers import Task, TasksController
from ..controllers.scenario_parser import ScenarioParser
from ..exceptions import WorkstationNotFound
from pydantic import BaseModel
import os, json

class Scenarios(BaseModel):
    scenarios: List[str]

class Scenario(BaseModel):
    name: str
    description: str


class TasksRouterBuilder:
    def __init__(self, tasksController: TasksController):
        self.tasksController: TasksController = tasksController
        self.scenarioParser: ScenarioParser = ScenarioParser()

    def build(self) -> APIRouter:
        router = APIRouter()

        @router.get("/tasklist/{workstation}", response_model=List[Task])
        async def listTasks(workstation: str):
            try:
                return self.tasksController.getQueue(workstation)
            except WorkstationNotFound:
                raise HTTPException(404, "Workstation not found")

        @router.post("/flushqueue/{workstation}")
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
            try:
                scenario: List[Task] = self.scenarioParser.parse_from_json_file(
                    f"./src/backend/assets/scenarios/{scenario_name}.json"
                )
            except FileNotFoundError:
                raise HTTPException(404, "Scenario not found")
            except Exception:
                raise HTTPException(500, "Invalid scenario format")
            for task in scenario:
                self.tasksController.addTask(workstation, task)
            self.tasksController.addTask(workstation, Task(
                action=TaskAction("end_scenario"),
                target=scenario_name,
                value=1
            ))

        @router.get("/scenarios")
        async def getScenarios():
            files = os.listdir("./src/backend/assets/scenarios")
            scenarios: List[Scenario] = []
            for file in files:
                with open(f"./src/backend/assets/scenarios/{file}", 'r') as openfile:
                    data = json.load(openfile)
                    description = data.get("description", "")
                    scenarios.append(Scenario(name=file.split('.json')[0], description=description))

            return scenarios

        return router
