import { Pool } from 'pg';

class DBService {
  private user: string;
  private password: string;
  private host: string;
  private port: number;
  private db: string;
  private pool: Pool;
  constructor(user: string, password: string, host: string, port: number, db: string) {
    this.user = user;
    this.password = password;
    this.host = host;
    this.port = port;
    this.db = db;
    this.pool = new Pool({
      host: this.host,
      user: this.user,
      password: this.password,
      port: this.port,
      database: this.db,
      max: 10,
    });
  }

  public runQuery = async (query: string) => {
    const result = await this.pool.query(query);
    return result;
  };
}

export default DBService;
