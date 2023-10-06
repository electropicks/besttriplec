import os
from enum import Enum

import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src import database as db
import dotenv

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)


class Column(Enum):
    POTIONS = 0
    ML = 1


@router.get("/inventory")
def get_inventory():
    """ """
    get_gold_sql = sqlalchemy.text("select gold from global_inventory")
    get_num_red_sql = sqlalchemy.text("select num_red_potions, num_red_ml from global_inventory")
    get_num_green_sql = sqlalchemy.text("select num_green_potions, num_green_ml from global_inventory")
    get_num_blue_sql = sqlalchemy.text("select num_blue_potions, num_blue_ml from global_inventory")
    with db.engine.begin() as connection:
        num_gold = connection.execute(get_gold_sql).one()[0]
        red = connection.execute(get_num_red_sql).one()
        print("red tuple:", red)
        num_red_potions, num_red_ml = red[Column.POTIONS.value], red[Column.ML.value]
        print("num_red_potions:", num_red_potions)
        print("num_red_ml:", num_red_ml)

        green = connection.execute(get_num_green_sql).one()
        print("green tuple:", green)
        num_green_potions, num_green_ml = green[Column.POTIONS.value], green[Column.ML.value]
        print("num_green_potions:", num_green_potions)
        print("num_green_ml:", num_green_ml)

        blue = connection.execute(get_num_blue_sql).one()
        print("blue tuple:", blue)
        num_blue_potions, num_blue_ml = blue[Column.POTIONS.value], blue[Column.ML.value]
        print("num_blue_potions:", num_blue_potions)
        print("num_blue_ml:", num_blue_ml)

    payload = {"number_of_red_potions": num_red_potions, "red_ml_in_barrels": num_red_ml,
               "number_of_green_potions": num_green_potions, "green_ml_in_barrels": num_green_ml,
               "number_of_blue_potions": num_blue_potions, "blue_ml_in_barrels": num_blue_ml,
               "gold": num_gold}
    return payload


class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool


# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
