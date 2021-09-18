#!/usr/bin/python

import psycopg2
from fastapi import FastAPI
import random
import configparser

config = configparser.RawConfigParser()
config.read("config.ini")
db_url = config["Server"].get("DatabaseUrl")

db = psycopg2.connect(dsn=db_url)
app = FastAPI()

@app.get("/recipes/")
async def root():
  # return random w/query parameters
  pass

@app.get("/recipes/{item_id}")
async def recipe_by_id(item_id: str):
  # return recipe by id unless it doesn't exist
  pass

