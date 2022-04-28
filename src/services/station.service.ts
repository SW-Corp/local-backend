import DBService from '../services/db.service';
import MetricsService from '../services/metrics.service';
import { DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB, INFLUX_ADDRESS, INFLUX_ORG, INFLUX_PORT, INFLUX_TOKEN} from '@config';
class StationService {
  private metricsService: MetricsService = new MetricsService(INFLUX_ADDRESS, parseInt(INFLUX_PORT), INFLUX_ORG, INFLUX_TOKEN);
  private dbService: DBService = new DBService(DB_USER, DB_PASSWORD, DB_HOST, parseInt(DB_PORT), DB);

  public getStation = async (name: string) => {
    const query = `SELECT * FROM Workstations WHERE name='${name}'`;
    const result = await this.dbService.runQuery(query);
    return result.rows;
  };

  public getMetrics = async (name: string) => {
    return this.metricsService.getMetrics();
  };
}

export default StationService;
