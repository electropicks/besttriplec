import random

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from src.api import auth
from src.api.audit import get_inventory
from src.database import SessionLocal, Base

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Assuming that your database's metadata is defined in your actual application
class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int


@router.post("/deliver")
async def post_deliver_bottles(potions_delivered: list[PotionInventory], db: Session = Depends(get_db)):
    """Receive deliveries of new potions, update the inventory, global catalog, and ledgers."""

    # Set a seller ID based on your business logic. For this example, it's a fixed value.
    seller_id = "besttriplec"

    # Retrieve the seller's global inventory
    global_inventory = db.query(GlobalInventory).filter_by(seller=seller_id).first()

    if not global_inventory:
        raise HTTPException(status_code=400, detail="No inventory record found for the seller.")

    for potion in potions_delivered:
        # Extract the potion details
        red_ml, green_ml, blue_ml, dark_ml = potion.potion_type
        quantity = potion.quantity

        # Check if this potion type already exists in the global catalog
        existing_potion = db.query(GlobalCatalog).filter(
            (GlobalCatalog.red_ml == red_ml) &
            (GlobalCatalog.green_ml == green_ml) &
            (GlobalCatalog.blue_ml == blue_ml) &
            (GlobalCatalog.dark_ml == dark_ml)
        ).first()

        if existing_potion:
            # The potion type exists; we need to increment the quantity in the global catalog.
            existing_potion.quantity += quantity
            potion_id_for_ledger = existing_potion.potion_id  # To be used in the potion ledger entry.
        else:
            # The potion type does not exist; we need to create a new record in the global catalog.
            new_potion = GlobalCatalog(
                red_ml=red_ml,
                green_ml=green_ml,
                blue_ml=blue_ml,
                dark_ml=dark_ml,
                quantity=quantity,
                sku=f"POT-{red_ml}-{green_ml}-{blue_ml}-{dark_ml}"
            )
            db.add(new_potion)
            db.flush()  # To get the new_potion.potion_id populated.
            potion_id_for_ledger = new_potion.potion_id

        # Record the transaction in the potion ledger
        potion_ledger_entry = PotionLedgerEntries(
            potion_id=potion_id_for_ledger,
            quantity_change=quantity,  # This assumes quantity is the change (i.e., new bottles delivered).
            description=f"Received delivery of {quantity} potions.",
            potion_sku=existing_potion.sku if existing_potion else new_potion.sku
        )
        db.add(potion_ledger_entry)

        # ... [Code for updating the global inventory and inventory ledger as previously described] ...

    # Commit the session to save all changes
    db.commit()

    return {"message": "Delivery processed and inventories updated successfully."}


# Gets called 4 times a day
@router.post("/plan")
async def get_bottle_plan():
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
GlobalInventory = Base.classes.global_inventory
PotionLedgerEntries = Base.classes.potion_ledger_entries
