import DBService from '../services/db.service'
import {DB_USER, DB_PASSWORD, DB_HOST, DB_PORT, DB} from '@config'
class StationService{
    private dbService: DBService;
    constructor(){
        this.dbService = new DBService(
            DB_USER,
            DB_PASSWORD,
            DB_HOST,
            parseInt(DB_PORT),
            DB,
        )
    }

    public getStation = async (name: string) => {
        const query = `SELECT * FROM Workstations WHERE name='${name}'`
        const result = await this.dbService.runQuery(query)
        return result.rows
    }
}

export default StationService;