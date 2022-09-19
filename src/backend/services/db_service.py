from dataclasses import dataclass

from psycopg2.extras import RealDictCursor
from psycopg2.pool import SimpleConnectionPool

from ..utils import get_logger

logger = get_logger("POSTGRES")


@dataclass
class DBConfig:
    port: int
    user: str
    password: str
    host: str
    db: str


@dataclass
class DBService:
    config: DBConfig

    def __post_init__(self):
        try:
            self.pool = SimpleConnectionPool(
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                host=self.config.host,
                database=self.config.db,
                minconn=1,
                maxconn=10,
            )
        except Exception as e:
            logger.error(
                f"Error connecting to DB ({self.config.host}:{self.config.port}): {e}"
            )
            exit(1)

    def run_query(self, query: str):
        connection = self.pool.getconn()
        if connection:
            cursor = connection.cursor(cursor_factory=RealDictCursor)
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            connection.close()
            return records
        else:
            raise Exception
