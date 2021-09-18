#!/usr/bin/python

import psycopg2
from fastapi import FastAPI
import random
import configparser
import json
from json.decoder import JSONDecodeError
from typing import List

config = configparser.RawConfigParser()
config.read("config.ini")
db_url = config["Server"].get("DatabaseUrl")

conn = psycopg2.connect(dsn=db_url)
app = FastAPI()

DB_COLUMNS = [
    ("id", str),
    ("name", str),
    ("imglink", str),
    ("prep_time", int),
    ("yield", int),
    ("description", str),
    ("ingredients", lambda i: json.loads(i)),
    ("steps", lambda i: json.loads(i)),
    ("source", str),
    ("vegan", bool),
    ("vegetarian", bool),
    ("halal", bool),
    ("treenut_free", bool),
    ("peanut_free", bool),
]


class Recipe:
    __slots__ = [i[0] for i in DB_COLUMNS]

    def __init__(self, *args):
        # it is assumed that there isn't going to be blank fields
        # they are at least populated with None
        # it is also assumed that the database schema *does not change*
        # update DB_COLUMNS if it does
        assert len(args) == len(DB_COLUMNS)

        for name, value in zip(DB_COLUMNS, args):
            try:
                self.__setattr__(name[0], name[1](value))
            except (TypeError, JSONDecodeError):
                # likely a conversion error from None
                self.__setattr__(name[0], None)

    def __iter__(self):
        return ((i, self.__getattribute__(i)) for i in self.__slots__)

    def __repr__(self):
        return str(dict(self))


def process_recipe_command(command: str) -> List[Recipe]:
    print(f"Running command {command}")
    try:
        cur = conn.cursor()
        cur.execute(command)
        rows = cur.fetchall()
        return list(map(lambda i: Recipe(*i), rows))
    except (psycopg2.Error) as error:
        print("Error while connecting to PostgreSQL", error)
    finally:
        if conn:
            cur.close()


@app.get("/recipes/")
def root(
    limit: int = 14,
    vegan: bool = False,
    vegetarian: bool = False,
    halal: bool = False,
    no_tree_nuts: bool = False,
    no_peanuts: bool = False,
):
    # return random w/query parameters
    # aiya
    extra_parameters = {
        "vegan": vegan,
        "vegetarian": vegetarian,
        "halal": halal,
        "treenutfree": no_tree_nuts,
        "peanutfree": no_peanuts,
    }

    select_query = "SELECT * FROM RECIPE WHERE id in (SELECT id FROM RECIPE"
    select_query2 = f"ORDER BY RANDOM() LIMIT {limit})"

    # this relies on the idea that False means anything is allowed
    # but True imposes a restriction
    filter_results = " AND ".join(
        map(
            lambda i: f"{i[0]}={str(i[1]).lower()}",
            filter(lambda i: i[1], extra_parameters.items()),
        )
    )

    if len(filter_results) > 0:
        # :(
        filter_results = f"WHERE {filter_results}"

    return process_recipe_command(
        " ".join((select_query, filter_results, select_query2, ";"))
    )


@app.get("/recipes/{item_id}")
def recipe_by_id(item_id: str):
    return process_recipe_command(f"SELECT * FROM RECIPE WHERE id={item_id};")


if __name__ == "__main__":
    print(root())
