import StationService from '../services/station.service';
import { NextFunction, Request, Response } from 'express';

class StationController {
  private stationService: StationService = new StationService();
  constructor() {
    console.log('init');
  }

  public getWorkstation = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const station = req.params['workstation'];

      if (!station) {
        res.status(400).json({ message: 'No workstation given' });
      } else {
        const stationInfo: string = await this.stationService.getStation(station);
        if (stationInfo) {
          res.status(201).json({ data: stationInfo, message: 'station' });
        } else {
          res.status(404).json({ data: '', message: 'No such station' });
        }
      }
    } catch (error) {
      next(error);
    }
  };

  public pushMetrics = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
      try {
        const station = req.params['workstation'];

        if (!station) {
          res.status(400).json({ message: 'No workstation given' });
        } else {
          const stationInfo: string = await this.stationService.pushMetrics(station);
          if (stationInfo) {
            res.status(201).json({ data: stationInfo, message: 'station' });
          } else {
            res.status(404).json({ data: '', message: 'No such station' });
          }
        }
      } catch (error) {
        next(error);
      }
    };
  

  public getMetrics = async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      const station = req.params['workstation'];

      if (!station) {
        res.status(400).json({ message: 'No workstation given' });
      } else {
        const stationInfo: string = await this.stationService.getMetrics(station);
        if (stationInfo) {
          res.status(201).json({ data: stationInfo, message: 'station' });
        } else {
          res.status(404).json({ data: '', message: 'No such station' });
        }
      }
    } catch (error) {
      next(error);
    }
  };
}

export default StationController;
