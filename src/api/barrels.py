import math
from collections import defaultdict
from dataclasses import dataclass
from random import randint
from typing import cast

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import update
from sqlalchemy.orm import Session

from src import database as db
from src.api import auth
from src.api.audit import get_inventory
from src.database import ProfessorCalls, GlobalInventory, get_db

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

RED = 0
GREEN = 1
BLUE = 2


@dataclass
class Option:
    color: int
    score: int

    def __lt__(self, other):
        return self.score < other.score

    def __eq__(self, other):
        return self.score == other.score


class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int


@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel], db: Session = Depends(db.get_db)):
    """ """
    # Loop through barrels delivered and update the global_inventory using ORM
    for barrel in barrels_delivered:
        if barrel.potion_type == [1, 0, 0, 0]:
            stmt = (
                update(GlobalInventory)
                .values(
                    red_ml=GlobalInventory.red_ml + barrel.ml_per_barrel * barrel.quantity,
                    checking_gold=GlobalInventory.checking_gold - barrel.price * barrel.quantity
                )
            )
            db.execute(stmt)

        elif barrel.potion_type == [0, 1, 0, 0]:
            stmt = (
                update(GlobalInventory)
                .values(
                    green_ml=GlobalInventory.green_ml + barrel.ml_per_barrel * barrel.quantity,
                    checking_gold=GlobalInventory.checking_gold - barrel.price * barrel.quantity
                )
            )
            db.execute(stmt)

        elif barrel.potion_type == [0, 0, 1, 0]:
            stmt = (
                update(GlobalInventory)
                .values(
                    blue_ml=GlobalInventory.blue_ml + barrel.ml_per_barrel * barrel.quantity,
                    checking_gold=GlobalInventory.checking_gold - barrel.price * barrel.quantity
                )
            )
            db.execute(stmt)

        elif barrel.potion_type == [0, 0, 0, 1]:
            stmt = (
                update(GlobalInventory)
                .values(
                    dark_ml=GlobalInventory.dark_ml + barrel.ml_per_barrel * barrel.quantity,
                    checking_gold=GlobalInventory.checking_gold - barrel.price * barrel.quantity
                )
            )
            db.execute(stmt)

    # Logging the professor's call
    prof_call = ProfessorCalls(
        endpoint="barrels/deliver",
        arguments={
            "barrels_delivered": barrels_delivered
        },
        response="OK"
    )
    db.add(prof_call)
    db.commit()

    return "OK"


def get_best_barrel_sku_and_price(barrels: dict[str, Barrel], gold_remaining: int) -> Barrel | None:
    if not barrels:
        return None
    highest_value_barrel = min(barrels.values(), key=lambda barrel: barrel.price)
    print("highest_value_barrel:", highest_value_barrel)
    if highest_value_barrel.price <= gold_remaining and highest_value_barrel.quantity > 0:
        return highest_value_barrel
    print("Can't buy highest_value_barrel.")
    print("looking for next most affordable")
    barrels.pop(highest_value_barrel.sku)
    print("updated barrels:", barrels)
    return get_best_barrel_sku_and_price(barrels, gold_remaining)


# Gets called once a day
def purchase_barrels(priority_option, wholesale_barrels, gold_remaining, to_buy):
    best_barrel = get_best_barrel_sku_and_price(wholesale_barrels[priority_option.color], gold_remaining)
    if best_barrel:
        to_buy[best_barrel.sku] += 1
        gold_remaining -= best_barrel.price
        priority_option.score += best_barrel.ml_per_barrel
        wholesale_barrels[priority_option.color][best_barrel.sku].quantity -= 1
        if wholesale_barrels[priority_option.color][best_barrel.sku].quantity == 0:
            del wholesale_barrels[priority_option.color][best_barrel.sku]
        if not wholesale_barrels[priority_option.color]:
            priority_option.score = math.inf
    return gold_remaining, to_buy


@router.post("/plan")
def get_wholesale_purchase(wholesale_catalog: list[Barrel], db: Session = Depends(get_db)):
    print(wholesale_catalog)
    inventory = get_inventory()
    print("inventory:", inventory)

    # Map potion types to colors
    potion_type_to_color = {
        (1, 0, 0, 0): RED,
        (0, 1, 0, 0): GREEN,
        (0, 0, 1, 0): BLUE
    }

    # Organize barrels by potion type
    wholesale_barrels = defaultdict(dict)
    for barrel in wholesale_catalog:
        color = potion_type_to_color[cast(tuple[int, int, int, int], tuple(barrel.potion_type))]

        wholesale_barrels[color][barrel.sku] = barrel

    gold_remaining = inventory["gold"]
    print("gold_remaining:", gold_remaining)

    red_score = Option(RED, randint(0, 100))
    green_score = Option(GREEN, randint(0, 100))
    blue_score = Option(BLUE, randint(0, 100))

    scores = [red_score, green_score, blue_score]
    to_buy = defaultdict(lambda: 0)

    while gold_remaining > 0.15 * inventory["gold"]:
        priority_option = min(scores, key=lambda x: x.score)
        if priority_option.score == math.inf:
            break
        gold_remaining, to_buy = purchase_barrels(priority_option, wholesale_barrels, gold_remaining, to_buy)

    list_to_buy = [{"sku": sku, "quantity": quantity} for sku, quantity in to_buy.items()]

    print("list_to_buy:", list_to_buy)
    print("gold remaining after purchase is made:", gold_remaining)

    prof_call = ProfessorCalls(
        endpoint="barrels/wholesale",
        arguments={
            "wholesale_catalog": wholesale_catalog
        },
        response=str(list_to_buy)
    )
    db.add(prof_call)
    db.commit()

    return list_to_buy
