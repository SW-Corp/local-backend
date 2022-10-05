from typing import List

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from backend.controllers.task_models import TaskAction

from ..controllers import Task, TasksController
from ..controllers.scenario_parser import ScenarioParser
from ..exceptions import WorkstationNotFound
from pydantic import BaseModel
import os, json


class Scenario(BaseModel):
    name: str
    description: str

class Scenarios(BaseModel):
    scenarios: List[Scenario]


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
                scenario, initial_conditions = self.scenarioParser.parse_from_json_file(
                    f"./src/backend/assets/scenarios/{scenario_name}.json"
                )
            except FileNotFoundError:
                raise HTTPException(404, "Scenario not found")
            except Exception:
                raise HTTPException(500, "Invalid scenario format")
            print(initial_conditions)
            self.tasksController.pushingThreads[workstation].currentScenario = scenario_name
            if not self.tasksController.pushingThreads[workstation].check_initial_conditions(initial_conditions):
                self.tasksController.pushingThreads[workstation].currentScenario = ""
                raise HTTPException(400, "Initial conditions not met")
            
            self.tasksController.addTask(workstation, Task(
                action=TaskAction("start_scenario"),
                target=scenario_name,
                value=1
            ))
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

            return Scenarios(scenarios=scenarios)

        @router.delete("/scenario/{scenarioname}")
        async def deleteScenario(scenarioname: str):
            files = os.listdir("./src/backend/assets/scenarios")
            if f"{scenarioname}.json" not in files:
                return HTTPException(404, "Scenario not found")
            try:
                os.remove(f"./src/backend/assets/scenarios/{scenarioname}.json")
            except Exception as e:
                return HTTPException(500, f"Error deleting scenario: {e}")

        @router.post("/addscenario/{scenarioname}")
        async def addScenario(scenarioname, request: Request):
            scenario = await request.json()
            if f"{scenario}.json" in os.listdir("./src/backend/assets/scenarios"):
                return HTTPException(400, f"Scenario already exists!")
            try:
                # validation
                self.scenarioParser.parse_from_json(scenario)
            except Exception as e:
                return HTTPException(400, f"Invalid scenario: {e}")

            try:
                file = open(f"./src/backend/assets/scenarios/{scenarioname}.json", "w")
                file.write(json.dumps(scenario))
                file.close()
            except Exception as e:
                return HTTPException(500, f"Error adding scenario {e}")
                
        @router.get("/scenario/{scenario_name}")
        async def getScenario(scenario_name: str):
            try:        
                with open(f"./src/backend/assets/scenarios/{scenario_name}.json", "r") as file:
                    data = json.load(file)
                    return data
            except FileNotFoundError:
                raise HTTPException(404, "Scenario not found")
            except Exception:
                raise HTTPException(500, "Error getting scenario")

        @router.post("/editscenario/{scenario_name}")
        async def editScenario(scenario_name: str, request: Request):
            if f"{scenario_name}.json" not in os.listdir("./src/backend/assets/scenarios"):
                raise HTTPException(404, "Scenario not found")

            scenario = await request.json()
            try:
                # validation
                print("pre validation")
                self.scenarioParser.parse_from_json(scenario)
                print("after validation")
            except Exception as e:
                raise HTTPException(400, f"Invalid scenario: {e}")

            try:
                print("writing")
                with open(f"./src/backend/assets/scenarios/{scenario_name}.json", "w") as file:
                    file.write(json.dumps(scenario))
                    print("write")
            except Exception as e:
                raise HTTPException(500, f"Error adding scenario {e}")


        return router
