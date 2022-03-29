import { Router } from 'express';
import StationController from '@controllers/station.controller';
import { Routes } from '@interfaces/routes.interface';
import authMiddleware from '@/middlewares/auth.middleware';

class WorkstationRoute implements Routes {
  public path = '/';
  public router = Router();
  private stationController: StationController = new StationController();

  constructor() {
    this.initializeRoutes();
  }

  private initializeRoutes() {
    this.router.get(`${this.path}workstation/:workstation`, authMiddleware, this.stationController.getWorkstation);
  }
}

export default WorkstationRoute;
