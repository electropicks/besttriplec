import sqlalchemy
from fastapi import APIRouter

from src.api.audit import get_inventory
from src import database as db

router = APIRouter()


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    get_num_red_potions_sql = sqlalchemy.text("select num_red_potions from global_inventory")
    get_num_green_potions_sql = sqlalchemy.text("select num_green_potions from global_inventory")
    get_num_blue_potions_sql = sqlalchemy.text("select num_blue_potions from global_inventory")
    with db.engine.begin() as connection:
        num_red_potions = connection.execute(get_num_red_potions_sql).one()[0]
        print("num_red_potions:", num_red_potions)
        num_green_potions = connection.execute(get_num_green_potions_sql).one()[0]
        print("num_green_potions:", num_green_potions)
        num_blue_potions = connection.execute(get_num_blue_potions_sql).one()[0]
        print("num_blue_potions:", num_blue_potions)
    # Can return a max of 20 items.
    payload = [
        {
            "sku": "RED_POTION_0",
            "name": "red potion",
            "quantity": num_red_potions,
            "price": 50,
            "potion_type": [100, 0, 0, 0],
        },
        {
            "sku": "GREEN_POTION_0",
            "name": "green potion",
            "quantity": num_green_potions,
            "price": 50,
            "potion_type": [0, 100, 0, 0],
        },
        {
            "sku": "BLUE_POTION_0",
            "name": "blue potion",
            "quantity": num_blue_potions,
            "price": 50,
            "potion_type": [0, 0, 100, 0],
        }

    ]
    print(payload)
    return payload
