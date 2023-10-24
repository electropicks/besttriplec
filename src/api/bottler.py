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
    Create a potion mix with random components ensuring the total is always 100ml.
    """
    inventory = get_inventory()  # This function should retrieve the current inventory status
    print("Starting with inventory:", inventory)

    potions_to_brew = []
    potion_components = ['red_ml_in_barrels', 'blue_ml_in_barrels', 'green_ml_in_barrels', 'dark_ml_in_barrels']

    # Calculating the total inventory for potion components
    total_inventory = sum(inventory[component] for component in potion_components if component in inventory)
    print(f"Total inventory for potion components: {total_inventory}ml")

    if total_inventory < 100:
        print("Not enough materials to make a 100ml potion.")
        raise HTTPException(status_code=400, detail="Not enough inventory to create a 100ml potion.")

    # Filter out the unavailable (zero inventory) components before planning the potions
    available_components = [component for component in potion_components if inventory.get(component, 0) > 0]
    print("Available components:", available_components)

    if not available_components:
        print("No components available to create a potion.")
        raise HTTPException(status_code=400, detail="No components available to create a potion.")

    # Calculate how many potions we can plan with the current inventory
    num_potions = total_inventory // 100
    print(f"Planning to create {num_potions} potion(s)")

    for potion_num in range(num_potions):
        print(f"\nCreating plan for potion {potion_num + 1}:")
        remaining = 100  # We want the sum of components to be 100 for each potion.
        potion_mix = {}

        for i, component in enumerate(available_components):
            available = inventory.get(component, 0)  # Get available inventory for this component.
            print(f"Inventory available for '{component}': {available}ml")

            if i == len(available_components) - 1:
                # If this is the last component, assign whatever is left to make the total 100.
                potion_mix[component] = remaining
                print(f"All remaining {remaining}ml assigned to '{component}'")
            else:
                # Randomly determine the component's share, but leave enough space to ensure
                # that the remaining components can still fill up to 100.
                space_for_others = len(available_components) - (i + 1)
                max_share = min(available, remaining - space_for_others)  # Can't use more than what's available.
                component_share = random.randint(1, max_share)  # At least 1 to ensure this component is present.

                print(f"Randomly selected {component_share}ml for '{component}'")
                potion_mix[component] = component_share
                remaining -= component_share

        # If we've reached this point, it means we have a valid potion mix for this iteration.
        print(f"\nGenerated potion mix for potion {potion_num + 1}: {potion_mix}")
        potions_to_brew.append({"potion_type": potion_mix, "quantity": 1})

    # Final report on potion planning
    print("\nCompleted potion planning. Summary:")
    for i, potion_plan in enumerate(potions_to_brew):
        print(f"Potion {i + 1}: {potion_plan}")

    return potions_to_brew


InventoryLedgerEntries = Base.classes.inventory_ledger_entries
GlobalCatalog = Base.classes.global_catalog
