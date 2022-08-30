import os

from dotenv import load_dotenv
from psycopg2 import pool

load_dotenv()


class DBController:
    def __init__(self):
        self.postgreSQL_pool = pool.SimpleConnectionPool(
            1,
            2,
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB"),
        )

    def execQuery(self, query):
        connection = self.postgreSQL_pool.getconn()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            records = cursor.fetchall()
            cursor.close()
            print("records", records)
            return records
        else:
            raise Exception


class DBService:
    def __init__(self):
        self.dbController = DBController()

    def getHashedPassword(self, email):
        query = f"SELECT password FROM Users WHERE email='{email}'"
        try:
            return self.dbController.execQuery(query)[0][0]
        except:
            return None

    def userExist(self, email):
        query = f"SELECT COUNT(*) FROM Users WHERE email='{email}'"
        try:
            return self.dbController.execQuery(query)[0][0]
        except:
            return None
