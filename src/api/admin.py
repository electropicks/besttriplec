from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api import auth
from src import database as db
import sqlalchemy

router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.post("/reset")
def reset(db: Session = Depends(db.get_db)):
    """
    Reset the game state. Gold goes to 100, all potions are removed from
    inventory, and all barrels are removed from inventory. Carts are all reset.
    """
    db.query(db.GlobalInventory).update(
        {
            "red_ml": 0,
            "green_ml": 0,
            "blue_ml": 0,
            "dark_ml": 0,
            "checking_gold": 100,
            "saving_gold": 0,
        })

    clear_inventory_sql = sqlalchemy.text(
        "update global_inventory set \
         red_ml = 0, \
         green_ml = 0, \
         blue_ml = 0, \
         dark_ml = 0, \
         checking_gold = 100, \
         saving_gold = 0"
    )
    print("clear_inventory_sql: ", clear_inventory_sql)
    clear_potions_sql = sqlalchemy.text("delete from global_catalog")
    print("clear_potions_sql: ", clear_potions_sql)
    clear_carts_sql = sqlalchemy.text("delete from global_carts")
    print("clear_carts_sql: ", clear_carts_sql)
    with db.engine.begin() as connection:
        connection.execute(clear_inventory_sql)
        print("Executed clear_inventory_sql")
        connection.execute(clear_potions_sql)
        print("Executed clear_potions_sql")
        connection.execute(clear_carts_sql)
        print("Executed clear_carts_sql")
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Best Triple C",
        "shop_owner": "The Potion Salesman",
    }

