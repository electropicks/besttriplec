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
    for potion in potions_delivered:
        red_ml = potion.potion_type[0]
        green_ml = potion.potion_type[1]
        blue_ml = potion.potion_type[2]
        dark_ml = potion.potion_type[3]
        sku = ""
        if red_ml > 0:
            sku += "RED_"
        if green_ml > 0:
            sku += "GREEN_"
        if blue_ml > 0:
            sku += "BLUE_"
        if dark_ml > 0:
            sku += "DARK_"
        sku += "POTION"
        quantity = potion.quantity
        print("Current potion, sku, quantity:", potion, sku, quantity)

        # Update the inventory
        update_inventory_sql = sqlalchemy.text(
            "update global_inventory set red_ml = red_ml - :red_ml, \
            green_ml = green_ml - :green_ml, \
            blue_ml = blue_ml - :blue_ml, \
            dark_ml = dark_ml - :dark_ml"
        )
        print("update_inventory_sql:", update_inventory_sql)

        # Check if there are already potions of this type in the catalog
        get_potion_existence_sql = sqlalchemy.text("select * from global_catalog where sku = :sku")
        print("get_potion_sql:", get_potion_existence_sql)

        with db.engine.begin() as connection:
            result = connection.execute(get_potion_existence_sql, {"sku": sku}).fetchall()
            print("Executed get_potion_sql")
            if len(result) == 0:
                # Add the potion to the catalog
                add_potion_sql = sqlalchemy.text(
                    "insert into global_catalog (sku, red_ml, green_ml, blue_ml, dark_ml, quantity) \
                    values (:sku, :red_ml, :green_ml, :blue_ml, :dark_ml, :quantity)"
                )
                print("add_potion_sql:", add_potion_sql)
                connection.execute(
                    add_potion_sql,
                    {"sku": sku, "red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml,
                     "quantity": quantity},
                )
                print("Executed add_potion_sql")
            else:
                # Update the quantity of the potion in the catalog
                update_potion_sql = sqlalchemy.text(
                    "update global_catalog set quantity = quantity + :quantity \
                    where sku = :sku"
                )
                print("update_potion_sql:", update_potion_sql)
                connection.execute(update_potion_sql, {"sku": sku, "quantity": quantity})
                print("Executed update_potion_sql")
            connection.execute(
                update_inventory_sql,
                {"red_ml": red_ml, "green_ml": green_ml, "blue_ml": blue_ml, "dark_ml": dark_ml},
            )
            print("Executed update_inventory_sql")
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

    potions_to_brew = []

    if inventory["red_ml_in_barrels"] >= 50 and inventory["blue_ml_in_barrels"] >= 50:
        potions_to_brew.append({"potion_type": [50, 0, 50, 0], "quantity": 1})
    elif inventory["red_ml_in_barrels"] >= 50 and inventory["green_ml_in_barrels"] >= 50:
        potions_to_brew.append({"potion_type": [50, 50, 0, 0], "quantity": 1})
    elif inventory["blue_ml_in_barrels"] >= 50 and inventory["green_ml_in_barrels"] >= 50:
        potions_to_brew.append({"potion_type": [0, 50, 50, 0], "quantity": 1})
    elif inventory["red_ml_in_barrels"] >= 100:
        potions_to_brew.append({"potion_type": [100, 0, 0, 0], "quantity": 1})
    elif inventory["green_ml_in_barrels"] >= 100:
        potions_to_brew.append({"potion_type": [0, 100, 0, 0], "quantity": 1})
    elif inventory["blue_ml_in_barrels"] >= 100:
        potions_to_brew.append({"potion_type": [0, 0, 100, 0], "quantity": 1})
    elif inventory["dark_ml_in_barrels"] >= 100:
        potions_to_brew.append({"potion_type": [0, 0, 0, 100], "quantity": 1})

    print("potions to brew:", potions_to_brew)
    return potions_to_brew
