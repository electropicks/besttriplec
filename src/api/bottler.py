import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src import database as db
from src.api import auth
from src.api.audit import get_inventory

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """ """
    print("potions delivered:", potions_delivered)
    red_potions_delivered = list(filter(lambda potion: potion.potion_type == [100, 0, 0, 0], potions_delivered))
    print("red_potions_delivered:", red_potions_delivered)
    green_potions_delivered = list(filter(lambda potion: potion.potion_type == [0, 100, 0, 0], potions_delivered))
    print("green_potions_delivered:", green_potions_delivered)
    blue_potions_delivered = list(filter(lambda potion: potion.potion_type == [0, 0, 100, 0], potions_delivered))
    print("blue_potions_delivered:", blue_potions_delivered)

    sqls_to_execute = []

    if red_potions_delivered:
        get_red_potions_sql = sqlalchemy.text(
            "update global_inventory set num_red_potions = num_red_potions + {0}, num_red_ml = num_red_ml - {0} * 100"
            .format(red_potions_delivered[0].quantity))
        print("get_red_potions_sql:", get_red_potions_sql)
        sqls_to_execute.append(get_red_potions_sql)
    if green_potions_delivered:
        get_green_potions_sql = sqlalchemy.text(
            "update global_inventory set num_green_potions = num_green_potions + {0}, num_green_ml = num_green_ml - {0} * 100"
            .format(green_potions_delivered[0].quantity))
        print("get_green_potions_sql:", get_green_potions_sql)
        sqls_to_execute.append(get_green_potions_sql)
    if blue_potions_delivered:
        get_blue_potions_sql = sqlalchemy.text(
            "update global_inventory set num_blue_potions = num_blue_potions + {0}, num_blue_ml = num_blue_ml - {0} * 100"
            .format(blue_potions_delivered[0].quantity))
        print("get_blue_potions_sql:", get_blue_potions_sql)
        sqls_to_execute.append(get_blue_potions_sql)

    with db.engine.begin() as connection:
        for sql in sqls_to_execute:
            connection.execute(sql)
            print("Executed sql:", sql)

    return "OK"


# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    inventory = get_inventory()
    print("inventory:", inventory)

    num_red_ml = inventory["red_ml_in_barrels"]
    num_red_potions_to_brew = num_red_ml // 100
    print("num_red_potions_to_brew:", num_red_potions_to_brew)
    num_green_ml = inventory["green_ml_in_barrels"]
    num_green_potions_to_brew = num_green_ml // 100
    print("num_green_potions_to_brew:", num_green_potions_to_brew)
    num_blue_ml = inventory["blue_ml_in_barrels"]
    num_blue_potions_to_brew = num_blue_ml // 100
    print("num_blue_potions_to_brew:", num_blue_potions_to_brew)

    payload = [
        {
            "potion_type": [100, 0, 0, 0],
            "quantity": num_red_potions_to_brew,
        },
        {
            "potion_type": [0, 100, 0, 0],
            "quantity": num_green_potions_to_brew,
        },
        {
            "potion_type": [0, 0, 100, 0],
            "quantity": num_blue_potions_to_brew,
        }
    ]

    print(payload)
    return payload
