import psycopg2
import configparser
import json
from typing import Optional, List

config = configparser.RawConfigParser()
config.read("config.ini")
db_url = config["Server"].get("DatabaseUrl")
table_name = config["Server"].get("DatabaseTable", fallback="RECIPE")

def dbstr(string: str):
    return rf"'{string}'"

CONVERTER = {
    "name": dbstr,
    "preptime": str,
    "ingredients": lambda i: dbstr(json.dumps(i)),
    "yield": str,
    "imglink": dbstr,
    "steps": lambda i: dbstr(i.split("\n")),
    "source": dbstr,
    #"nutrients": lambda i: dbstr(json.dumps(i)), NOT IMPLEMENTED
}

DIETARY_RESTRICTIONS = {
    "vegan": "vegan",
    "vegetarian": "vegetarian",
    "no_tree_nuts": "treenutfree",
    "no_peanuts": "peanutfree",
    "no_dairy": "dairyfree",
    "halal": "halal"
}

class Uploader:
    def __init__(self, json_read: str = None):
        self.json: dict = json.load(json_read) if json_read else None
        if self.json:
            print(f"Loaded {json_read}")
        self.conn = psycopg2.connect(dsn=db_url)

    def push(self, json: Optional[dict] = None):
        final_json = json
        if not final_json:
            raise ValueError("Incorrectly formed or JSON not provided")
        for k in list(CONVERTER.keys()) + list(DIETARY_RESTRICTIONS.keys()):
            if not k in final_json:
                raise AssertionError(f"Missing field {k}")
        for k in list(final_json.keys()):
            if not (k in CONVERTER or k in DIETARY_RESTRICTIONS):
                print(f"WARN: Extra field {k}, skipping it")
                del final_json[k]

        columns, values = map(lambda i: DIETARY_RESTRICTIONS[i] if i in DIETARY_RESTRICTIONS else i, final_json.keys()), list(map(lambda i: str(CONVERTER[i[0]](i[1]) if i[0] in CONVERTER else dbstr(i[1]).lower()), final_json.items()))
        print(values)

        command = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
        print(f"Executing {command}")
        try:
            cur = self.conn.cursor()
            cur.execute(command)
            self.conn.commit()
            print(f"Successfully executed command")
        except psycopg2.Error as err:
            print(f"An error occurred: {err}")
        finally:
            cur.close()


if __name__ == "__main__":
    uploader = Uploader()
    uploader.push(json.loads('''{
    "imglink": "https://imagesvc.meredithcorp.io/v3/mm/image?url=https%3A%2F%2Fimages.media-allrecipes.com%2Fuserphotos%2F7324353.jpg",
    "name": "Lighter Mushroom Tortellini Alfredo",
    "preptime": 15,
    "ingredients": {
        "spaghetti": {
            "quantity": 1.0,
            "unit": "pound",
            "calories": 1682.8276927000002
        },
        "garlic": {
            "quantity": 6.0,
            "unit": "clove",
            "calories": 26.82
        },
        "olive oil": {
            "quantity": 0.5,
            "unit": "cup",
            "calories": 954.72
        },
        "red pepper flakes": {
            "quantity": 0.25,
            "unit": "teaspoon",
            "calories": 0.624375000031669
        },
        "salt": {
            "quantity": "null",
            "unit": "null",
            "calories": 0.0
        },
        "parsley": {
            "quantity": 0.25,
            "unit": "cup",
            "calories": 5.4
        },
        "Parmigiano-Reggiano cheese": {
            "quantity": 1.0,
            "unit": "cup",
            "calories": 582.9285000000001
        }
    },
    "steps": "abc",
    "yield": 3,
    "source": "https://www.allrecipes.com/recipe/277448",
    "nutrients": {
        "calories": "496.8 calories",
        "carbohydrateContent": "46.9 g",
        "cholesterolContent": "87.3 mg",
        "fatContent": "24.9 g",
        "fiberContent": "2.5 g",
        "proteinContent": "23.4 g",
        "saturatedFatContent": "14.6 g",
        "sodiumContent": "759.1 mg",
        "sugarContent": "7.5 g"
    },
    "vegan": false,
    "vegetarian": true,
    "no_tree_nuts": true,
    "no_peanuts": true,
    "no_dairy": false,
    "halal": true
}'''))
