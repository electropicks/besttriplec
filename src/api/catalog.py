from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from src.database import get_db, GlobalCatalog

router = APIRouter()

RED = 1
GREEN = 2
BLUE = 3
DARK = 4
QUANTITY = 5


@router.get("/catalog/", tags=["catalog"])
def get_catalog(db: Session = Depends(get_db)):
    potions = db.query(GlobalCatalog).filter(GlobalCatalog.quantity > 0).all()

    payload = []
    for potion in potions:
        sku = ""
        if potion.red > 0:
            sku += "RED_"
        if potion.green > 0:
            sku += "GREEN_"
        if potion.blue > 0:
            sku += "BLUE_"
        if potion.dark > 0:
            sku += "DARK_"
        sku += "POTION"
        payload.append(
            {
                "sku": sku,
                "name": sku.lower(),
                "quantity": potion.quantity,
                "price": 50,
                "potion_type": [potion.red, potion.green, potion.blue, potion.dark],
            }
        )

    return payload
