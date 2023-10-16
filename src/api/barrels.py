import math
from random import randint
from collections import defaultdict

import sqlalchemy
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from dataclasses import dataclass

from src import database as db
from src.api import auth
from src.api.audit import get_inventory

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
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    """ """
    print("barrels_delivered", barrels_delivered)

    red_barrels_delivered = list(filter(lambda barrel: barrel.potion_type == [1, 0, 0, 0], barrels_delivered))
    print("red_barrels_delivered:", red_barrels_delivered)
    if red_barrels_delivered:
        for red_barrel in red_barrels_delivered:
            buy_red_barrel_sql = sqlalchemy.text(
                "update global_inventory set num_red_ml = num_red_ml + {0} * {1}, gold = gold - {2} * {1}".format(
                    red_barrel.ml_per_barrel, red_barrel.quantity, red_barrel.price))
            print("buy_red_barrel_sql:", buy_red_barrel_sql)
            with db.engine.begin() as connection:
                connection.execute(buy_red_barrel_sql)
                print("Executed buy_red_barrel_sql")

    green_barrels_delivered = list(filter(lambda barrel: barrel.potion_type == [0, 1, 0, 0], barrels_delivered))
    print("green_barrels_delivered:", green_barrels_delivered)
    if green_barrels_delivered:
        for green_barrel in green_barrels_delivered:
            buy_green_barrel_sql = sqlalchemy.text(
                "update global_inventory set num_green_ml = num_green_ml + {0} * {1}, gold = gold - {2} * {1}".format(
                    green_barrel.ml_per_barrel, green_barrel.quantity, green_barrel.price))
            print("buy_green_barrel_sql:", buy_green_barrel_sql)
            with db.engine.begin() as connection:
                connection.execute(buy_green_barrel_sql)
                print("Executed buy_green_barrel_sql")

    blue_barrels_delivered = list(filter(lambda barrel: barrel.potion_type == [0, 0, 1, 0], barrels_delivered))
    print("blue_barrels_delivered:", blue_barrels_delivered)
    if blue_barrels_delivered:
        for blue_barrel in blue_barrels_delivered:
            buy_blue_barrel_sql = sqlalchemy.text(
                "update global_inventory set num_blue_ml = num_blue_ml + {0} * {1}, gold = gold - {2} * {1}".format(
                    blue_barrel.ml_per_barrel, blue_barrel.quantity, blue_barrel.price))
            print("buy_blue_barrel_sql:", buy_blue_barrel_sql)
            with db.engine.begin() as connection:
                connection.execute(buy_blue_barrel_sql)
                print("Executed buy_blue_barrel_sql")

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
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    """ """
    print(wholesale_catalog)
    inventory = get_inventory()
    print("inventory:", inventory)
    wholesale_red_barrels = list(filter(lambda barrel: barrel.potion_type == [1, 0, 0, 0], wholesale_catalog))
    wholesale_red_barrels = {barrel.sku: barrel for barrel in wholesale_red_barrels}
    wholesale_green_barrels = list(filter(lambda barrel: barrel.potion_type == [0, 1, 0, 0], wholesale_catalog))
    wholesale_green_barrels = {barrel.sku: barrel for barrel in wholesale_green_barrels}
    wholesale_blue_barrels = list(filter(lambda barrel: barrel.potion_type == [0, 0, 1, 0], wholesale_catalog))
    wholesale_blue_barrels = {barrel.sku: barrel for barrel in wholesale_blue_barrels}
    print("wholesale_red_barrels:", wholesale_red_barrels)
    print("wholesale_green_barrels:", wholesale_green_barrels)
    print("wholesale_blue_barrels:", wholesale_blue_barrels)

    gold_remaining = inventory["gold"]
    print("gold_remaining:", gold_remaining)

    # red_score = Option(RED, inventory["number_of_red_potions"] * 100 + inventory["red_ml_in_barrels"])
    # red_score = Option(RED, 100000)
    # green_score = Option(GREEN, inventory["number_of_green_potions"] * 100 + inventory["green_ml_in_barrels"])
    # blue_score = Option(BLUE, inventory["number_of_blue_potions"] * 100 + inventory["blue_ml_in_barrels"])
    red_score = Option(RED, randint(0, 100))
    green_score = Option(GREEN, randint(0, 100))
    blue_score = Option(BLUE, randint(0, 100))
    print("red_score:", red_score)
    print("green_score:", green_score)
    print("blue_score:", blue_score)

    to_buy = defaultdict(lambda: 0)

    while gold_remaining > 0.15 * inventory["gold"]:
        priority_option = min(red_score, green_score, blue_score)
        print("priority_option:", priority_option)

        if priority_option.color == RED:
            best_red_barrel = get_best_barrel_sku_and_price(wholesale_red_barrels, gold_remaining)
            if best_red_barrel:
                to_buy[best_red_barrel.sku] += 1
                gold_remaining -= best_red_barrel.price
                print("Purchasing red barrel:", best_red_barrel.sku, "for", best_red_barrel.price, "gold.")
                print("gold_remaining:", gold_remaining)
                red_score.score += best_red_barrel.ml_per_barrel
                print("red_score:", red_score)
                wholesale_red_barrels[best_red_barrel.sku].quantity -= 1
                if wholesale_red_barrels[best_red_barrel.sku].quantity == 0:
                    wholesale_red_barrels.pop(best_red_barrel.sku)
                if not wholesale_red_barrels:
                    print("wholesale_red_barrels is empty")
                    red_score.score = math.inf
                continue
            break

        elif priority_option.color == GREEN:
            best_green_barrel = get_best_barrel_sku_and_price(wholesale_green_barrels, gold_remaining)
            if best_green_barrel:
                to_buy[best_green_barrel.sku] += 1
                gold_remaining -= best_green_barrel.price
                print("Purchasing green barrel:", best_green_barrel.sku, "for", best_green_barrel.price, "gold.")
                print("gold_remaining:", gold_remaining)
                green_score.score += best_green_barrel.ml_per_barrel
                print("green_score:", green_score)
                wholesale_green_barrels[best_green_barrel.sku].quantity -= 1
                if wholesale_green_barrels[best_green_barrel.sku].quantity == 0:
                    wholesale_green_barrels.pop(best_green_barrel.sku)
                if not wholesale_green_barrels:
                    print("wholesale_green_barrels is empty")
                    green_score.score = math.inf
                continue
            break

        elif priority_option.color == BLUE:
            best_blue_barrel = get_best_barrel_sku_and_price(wholesale_blue_barrels, gold_remaining)
            if best_blue_barrel:
                to_buy[best_blue_barrel.sku] += 1
                gold_remaining -= best_blue_barrel.price
                print("Purchasing blue barrel:", best_blue_barrel.sku, "for", best_blue_barrel.price, "gold.")
                print("gold_remaining:", gold_remaining)
                blue_score.score += best_blue_barrel.ml_per_barrel
                print("blue_score:", blue_score)
                wholesale_blue_barrels[best_blue_barrel.sku].quantity -= 1
                if wholesale_blue_barrels[best_blue_barrel.sku].quantity == 0:
                    wholesale_blue_barrels.pop(best_blue_barrel.sku)
                if not wholesale_blue_barrels:
                    print("wholesale_blue_barrels is empty")
                    blue_score.score = math.inf
                continue
            break

    print("to_buy:", to_buy)
    # convert default dict into list of objects of format {"sku": string, "quantity": int}
    list_to_buy = [{"sku": sku, "quantity": quantity} for sku, quantity in to_buy.items()]

    print("list_to_buy:", list_to_buy)
    print("gold remaining after purchase is made:", gold_remaining)
    return list_to_buy
