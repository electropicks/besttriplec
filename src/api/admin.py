from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.api import auth
from src import database as db
import sqlalchemy

from src.database import GlobalInventory, GlobalCatalog, GlobalCarts, InventoryLedgerEntries

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
    db.query(GlobalInventory).update(
        {
            "red_ml": 0,
            "green_ml": 0,
            "blue_ml": 0,
            "dark_ml": 0,
            "checking_gold": 100,
            "saving_gold": 0,
        })
    db.query(GlobalCatalog).delete()
    db.query(GlobalCarts).delete()
    db.commit()
    return "OK"


@router.get("/shop_info/")
def get_shop_info():
    """ """

    return {
        "shop_name": "Best Triple C",
        "shop_owner": "The Potion Salesman",
    }

