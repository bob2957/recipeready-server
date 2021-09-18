import psycopg2
import configparser
import json
from typing import Optional

config = configparser.RawConfigParser()
config.read("config.ini")
db_url = config["Server"].get("DatabaseUrl")
table_name = config["Server"].get("DatabaseTable", fallback="RECIPE")
json_read = config["Server"].get("JsonFile", fallback=False)


class Uploader:
    def __init__(self):
        self.json: dict = json.load(json_read) if json_read else None
        if self.json:
            print(f"Loaded {json_read}")
        self.conn = psycopg2.connect(dsn=db_url)

    def push(self, json: Optional[dict] = None):
        final_json = json or self.json
        command = f"INSERT INTO {table_name}"
        print(f"Executing {command}")
        try:
            cur = self.conn.cursor()
            cur.execute(command)
            print(f"Successfully executed {command}")
        except psycopg2.Error as err:
            print(f"An error occurred: {err}")
        finally:
            cur.close()

if __name__ == "__main__":
    uploader = Uploader()
    uploader.push()
