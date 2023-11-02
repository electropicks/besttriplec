from enum import Enum

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from src.api import auth
from src.database import ProfessorCalls, get_db, GlobalInventory, GlobalCatalog

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)


class Column(Enum):
    POTIONS = 0
    ML = 1


@router.get("/inventory")
def get_inventory(db: Session = Depends(get_db)):
    """ """
    # Fetching gold from global_inventory using ORM
    num_gold = db.query(GlobalInventory.checking_gold).first()[0]

    # Fetching number of red, green, blue, and dark potions from global_catalog using ORM
    num_red_potions = db.query(GlobalCatalog).filter(GlobalCatalog.red_ml == 100).count()
    num_green_potions = db.query(GlobalCatalog).filter(GlobalCatalog.green_ml == 100).count()
    num_blue_potions = db.query(GlobalCatalog).filter(GlobalCatalog.blue_ml == 100).count()
    num_dark_potions = db.query(GlobalCatalog).filter(GlobalCatalog.dark_ml == 100).count()

    # Fetching ml of red, green, blue, and dark potions from global_inventory using ORM
    num_red_ml = db.query(GlobalInventory.red_ml).first()[0]
    num_green_ml = db.query(GlobalInventory.green_ml).first()[0]
    num_blue_ml = db.query(GlobalInventory.blue_ml).first()[0]
    num_dark_ml = db.query(GlobalInventory.dark_ml).first()[0]

    # Construct the payload
    payload = {
        "number_of_red_potions": num_red_potions,
        "red_ml_in_barrels": num_red_ml,
        "number_of_green_potions": num_green_potions,
        "green_ml_in_barrels": num_green_ml,
        "number_of_blue_potions": num_blue_potions,
        "blue_ml_in_barrels": num_blue_ml,
        "number_of_dark_potions": num_dark_potions,
        "dark_ml_in_barrels": num_dark_ml,
        "gold": num_gold
    }
    # Logging the professor's call
    prof_call = ProfessorCalls(
        endpoint="audit/inventory",
        arguments={},
        response=str(payload)
    )
    db.add(prof_call)
    db.commit()

    return payload


# Returning the modified function to get feedback before proceeding further

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool


# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
