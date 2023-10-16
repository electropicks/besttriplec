import sqlalchemy
from fastapi import APIRouter

from src.api.audit import get_inventory
from src import database as db

router = APIRouter()

RED = 1
GREEN = 2
BLUE = 3
DARK = 4
QUANTITY = 5


@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    get_potions_sql = sqlalchemy.text("select * from global_catalog where quantity > 0")
    with db.engine.begin() as connection:
        result = connection.execute(get_potions_sql).fetchall()
    payload = []
    for row in result:
        sku = ""
        if row[RED] > 0:
            sku += "RED_"
        if row[GREEN] > 0:
            sku += "GREEN_"
        if row[BLUE] > 0:
            sku += "BLUE_"
        if row[DARK] > 0:
            sku += "DARK_"
        sku += "POTION"
        payload.append(
            {
                "sku": sku,
                "name": sku.lower(),
                "quantity": row[QUANTITY],
                "price": 50,
                "potion_type": [row[RED], row[GREEN], row[BLUE], row[DARK]],
            }
        )

    print(payload)
    return payload
