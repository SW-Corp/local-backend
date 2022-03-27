import { Router } from 'express';
import StationController from '@controllers/station.controller';
import { Routes } from '@interfaces/routes.interface';
import authMiddleware from '@/middlewares/auth.middleware';

class WorkstationRoute implements Routes {
    public path = '/';
    public router = Router();
    public stationController;
  
    constructor() {
      this.stationController = new StationController();
      this.initializeRoutes();
    }
  
    private initializeRoutes() {
      this.router.get(`${this.path}workstation/:workstation`, authMiddleware, this.stationController.getWorkstation);
      // this.router.get(`${this.path}/workstation`, authMiddleware, ()=>{console.log("egh")});
    }
  }
  
  export default WorkstationRoute;