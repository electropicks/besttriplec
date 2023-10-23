import random
from sqlalchemy import insert, select, update
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src import database as db
from src.api import auth
from src.api.audit import get_inventory
from src.database import global_catalog, global_inventory

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


# Assuming that your database's metadata is defined in your actual application
class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    """Receive deliveries of new potions and update the inventory."""
    print("potions delivered:", potions_delivered)
    for potion in potions_delivered:
        red_ml = potion.potion_type[0]
        green_ml = potion.potion_type[1]
        blue_ml = potion.potion_type[2]
        dark_ml = potion.potion_type[3]

        sku = f"r{red_ml}g{green_ml}b{blue_ml}d{dark_ml}"

        quantity = potion.quantity
        print("Current potion, sku, quantity:", potion, sku, quantity)

        with db.engine.begin() as connection:
            # Check if the potion already exists in the catalog
            get_potion_stmt = select([global_catalog]).where(global_catalog.c.sku == sku)
            result = connection.execute(get_potion_stmt).fetchall()
            print("Executed get_potion_sql")

            if len(result) == 0:
                # Potion doesn't exist, insert a new record
                add_potion_stmt = insert(global_catalog).values(
                    sku=sku,
                    red_ml=red_ml,
                    green_ml=green_ml,
                    blue_ml=blue_ml,
                    dark_ml=dark_ml,
                    quantity=quantity
                )
                connection.execute(add_potion_stmt)
                print("Executed add_potion_sql")
            else:
                # Potion exists, update the quantity
                update_potion_stmt = (
                    update(global_catalog)
                    .where(global_catalog.c.sku == sku)
                    .values(quantity=global_catalog.c.quantity + quantity)
                )
                connection.execute(update_potion_stmt)
                print("Executed update_potion_sql")

            # Update the inventory
            update_inventory_stmt = (
                update(global_inventory)
                .values(
                    red_ml=global_inventory.c.red_ml - red_ml,
                    green_ml=global_inventory.c.green_ml - green_ml,
                    blue_ml=global_inventory.c.blue_ml - blue_ml,
                    dark_ml=global_inventory.c.dark_ml - dark_ml
                )
            )
            connection.execute(update_inventory_stmt)
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
    print("Current inventory:", inventory)

    # Calculate the total inventory.
    total_inventory = sum(inventory.values())

    potions_to_brew = []

    # Continue bottling as long as there's sufficient inventory.
    while total_inventory >= 100:
        # Create a potion mix by selecting a random percentage of each type.
        red_percentage = random.randint(0, min(100, inventory["red_ml_in_barrels"]))
        blue_percentage = random.randint(0, min(100 - red_percentage, inventory["blue_ml_in_barrels"]))
        green_percentage = random.randint(0,
                                          min(100 - red_percentage - blue_percentage, inventory["green_ml_in_barrels"]))
        dark_percentage = random.randint(0, min(100 - red_percentage - blue_percentage - green_percentage,
                                                inventory["dark_ml_in_barrels"]))

        # Determine the quantity for this batch based on the smallest amount necessary according to percentages.
        quantity = min(inventory["red_ml_in_barrels"] * red_percentage // 100,
                       inventory["blue_ml_in_barrels"] * blue_percentage // 100,
                       inventory["green_ml_in_barrels"] * green_percentage // 100,
                       inventory["dark_ml_in_barrels"] * dark_percentage // 100)

        # If we have a valid potion, add it to the brew list
        if quantity > 0:
            potion_to_add = {"potion_type": [red_percentage, blue_percentage, green_percentage, dark_percentage],
                             "quantity": quantity}
            potions_to_brew.append(potion_to_add)

            # Recalculate the total inventory.
            total_inventory = sum(inventory.values())
        else:
            break  # No potions can be made, exit the loop.

    # Check if the total inventory is less than 100ml, and if not, raise an exception.
    if total_inventory >= 100:
        raise HTTPException(status_code=400, detail="The total inventory could not be reduced below 100ml.")

    print("Final potions to brew:", potions_to_brew)
    print("Updated inventory:", inventory)

    return potions_to_brew
