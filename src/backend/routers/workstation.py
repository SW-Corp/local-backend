from backend.controllers import workstation
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from ..controllers import MetricsList, WorkstationController
from ..exceptions import WorkstationNotFound
import os

class WorkstationRouterBuilder:
    def __init__(self, worstationController: WorkstationController):
        self.worstationController: WorkstationController = worstationController

    def build(self) -> APIRouter:
        router = APIRouter()

        @router.get("/workstation/{stationname}")
        async def getWorkstation(stationname: str):
            try:
                stationData = self.worstationController.getStation(stationname)
            except WorkstationNotFound:
                raise HTTPException(404, "Workstation not found")
            return stationData
            pass

        @router.get("/workstations")
        async def getWorstations():
            return self.worstationController.getWorkstations()

        @router.post("/metrics")
        async def pushMetrics(metricsList: MetricsList):
            await self.worstationController.pushMetrics(metricsList)
            return Response(status_code=201)

        @router.get("/metrics/{stationname}")
        async def pullMetrics(stationname):
            return self.worstationController.pullMetrics(stationname)

        @router.post("/shutdown")
        async def shutdown():
            os.system("echo true > /shutdown_signal")

        @router.post("/calibrate/{station}/{container}")
        async def calibrate(station, container):
            self.worstationController.calibrateSensor(station, container)

        @router.get("/logs")
        async def getLogs():
            return self.worstationController.getLogs()

        return router
