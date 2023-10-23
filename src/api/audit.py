from enum import Enum

import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src import database as db
from src.api import auth

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
    get_gold_sql = sqlalchemy.text("select checking_gold from global_inventory")
    get_num_red_potions_sql = sqlalchemy.text("select * from global_catalog where red_ml = 100")
    get_num_green_potions_sql = sqlalchemy.text("select * from global_catalog where green_ml = 100")
    get_num_blue_potions_sql = sqlalchemy.text("select * from global_catalog where blue_ml = 100")
    # Added: query for fetching dark potions where dark_ml is 100.
    get_num_dark_potions_sql = sqlalchemy.text("select * from global_catalog where dark_ml = 100")

    get_num_red_ml_sql = sqlalchemy.text("select red_ml from global_inventory")
    get_num_green_ml_sql = sqlalchemy.text("select green_ml from global_inventory")
    get_num_blue_ml_sql = sqlalchemy.text("select blue_ml from global_inventory")
    # Added: query for fetching the total dark_ml in inventory.
    get_num_dark_ml_sql = sqlalchemy.text("select dark_ml from global_inventory")

    with db.engine.begin() as connection:
        num_red_potions = len(connection.execute(get_num_red_potions_sql).fetchall())
        print("num_red_potions:", num_red_potions)
        num_green_potions = len(connection.execute(get_num_green_potions_sql).fetchall())
        print("num_green_potions:", num_green_potions)
        num_blue_potions = len(connection.execute(get_num_blue_potions_sql).fetchall())
        print("num_blue_potions:", num_blue_potions)
        # Added: fetching the number of dark potions.
        num_dark_potions = len(connection.execute(get_num_dark_potions_sql).fetchall())
        print("num_dark_potions:", num_dark_potions)

        num_red_ml = connection.execute(get_num_red_ml_sql).one()[0]
        print("num_red_ml:", num_red_ml)
        num_green_ml = connection.execute(get_num_green_ml_sql).one()[0]
        print("num_green_ml:", num_green_ml)
        num_blue_ml = connection.execute(get_num_blue_ml_sql).one()[0]
        print("num_blue_ml:", num_blue_ml)
        # Added: fetching the total dark_ml in inventory.
        num_dark_ml = connection.execute(get_num_dark_ml_sql).one()[0]
        print("num_dark_ml:", num_dark_ml)

        num_gold = connection.execute(get_gold_sql).one()[0]
        print("num_gold:", num_gold)

    # Construct the payload to include information about the dark potions and ml.
    payload = {"number_of_red_potions": num_red_potions, "red_ml_in_barrels": num_red_ml,
               "number_of_green_potions": num_green_potions, "green_ml_in_barrels": num_green_ml,
               "number_of_blue_potions": num_blue_potions, "blue_ml_in_barrels": num_blue_ml,
               "number_of_dark_potions": num_dark_potions, "dark_ml_in_barrels": num_dark_ml,  # Added dark potion info
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
