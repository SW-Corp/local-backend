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
            connection.close()
            return records
        else:
            raise Exception

    def run_query_insert(self, query: str):
        connection = self.postgreSQL_pool.getconn()
        if connection:
            cursor = connection.cursor()
            cursor.execute(query)
            connection.commit()
            cursor.close()
            connection.close()
        else:
            raise Exception


class DBService:
    def __init__(self):
        self.dbController = DBController()

    def getHashedPassword(self, email):
        query = f"SELECT password FROM Users WHERE email='{email}'"
        try:
            return self.dbController.execQuery(query)[0][0]
        except Exception:
            return None

    def getPermission(self, email):
        query = f"SELECT permission FROM Users WHERE email='{email}'"
        return self.dbController.execQuery(query)[0][0]


    def checkPermission(self, email, permission):
        permission_levels = {
            "read": ["read"],
            "write": ["read", "write"],
            "manage_users": ["read", "write", "manage_users"],
        }
        query = f"SELECT permission FROM Users WHERE email='{email}'"

        try:
            if (
                permission
                in permission_levels[self.dbController.execQuery(query)[0][0]]
            ):
                return True
            else:
                return False
        except Exception:
            return False

    def signup(self, email, password):
        self.dbController.run_query_insert(
            f"INSERT INTO USERS (email, password, permission) VALUES ('{email}', '{password}', 'read')"
        )
