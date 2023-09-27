import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from src import database as db
from src.api import auth
from src.api.audit import get_inventory

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print(barrels_delivered)
    for barrel in barrels_delivered:
        update_inventory_sql = sqlalchemy.text("update global_inventory set num_red_ml = {0}, gold = gold - {1}"
                                               .format(barrel.ml_per_barrel * barrel.quantity,
                                                       barrel.price * barrel.quantity)
                                               )
        print("update_inventory_sql for barrel:", barrel, ": ", update_inventory_sql)
        with db.engine.begin() as connection:
            connection.execute(update_inventory_sql)
            print("Executed update_inventory_sql for barrel:", barrel)
    return "OK"


# Gets called once a day
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    inventory = get_inventory()
    to_buy = inventory["gold"] // list(filter(
        lambda barrel: barrel.potion_type == [100, 0, 0, 0]
        , wholesale_catalog))[0].price
    if inventory["number_of_potions"] >= 10:
        to_buy = 0
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": to_buy,
        }
    ]
