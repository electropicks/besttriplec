import sqlalchemy
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src import database as db
from src.api import auth
from enum import Enum

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)

class search_sort_options(str, Enum):
    customer_name = "customer_name"
    item_sku = "item_sku"
    line_item_total = "line_item_total"
    timestamp = "timestamp"

class search_sort_order(str, Enum):
    asc = "asc"
    desc = "desc"   

@router.get("/search/", tags=["search"])
def search_orders(
    customer_name: str = "",
    potion_sku: str = "",
    search_page: str = "",
    sort_col: search_sort_options = search_sort_options.timestamp,
    sort_order: search_sort_order = search_sort_order.desc,
):
    """
    Search for cart line items by customer name and/or potion sku.

    Customer name and potion sku filter to orders that contain the 
    string (case insensitive). If the filters aren't provided, no
    filtering occurs on the respective search term.

    Search page is a cursor for pagination. The response to this
    search endpoint will return previous or next if there is a
    previous or next page of results available. The token passed
    in that search response can be passed in the next search request
    as search page to get that page of results.

    Sort col is which column to sort by and sort order is the direction
    of the search. They default to searching by timestamp of the order
    in descending order.

    The response itself contains a previous and next page token (if
    such pages exist) and the results as an array of line items. Each
    line item contains the line item id (must be unique), item sku, 
    customer name, line item total (in gold), and timestamp of the order.
    Your results must be paginated, the max results you can return at any
    time is 5 total line items.
    """

    return {
        "previous": "",
        "next": "",
        "results": [
            {
                "line_item_id": 1,
                "item_sku": "1 oblivion potion",
                "customer_name": "Scaramouche",
                "line_item_total": 50,
                "timestamp": "2021-01-01T00:00:00Z",
            }
        ],
    }


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    """ """
    print("calling create_cart with new_cart:", new_cart)
    customer_name = new_cart.customer
    create_cart_sql = sqlalchemy.text(
        "insert into global_carts(customer_name, created_at) values(:customer_name, now())"
    )
    print("create_cart_sql:", create_cart_sql)
    get_cart_id_sql = sqlalchemy.text(
        "select max(cart_id) from global_carts where customer_name = :customer_name"
    )
    with db.engine.begin() as connection:
        connection.execute(create_cart_sql, {"customer_name": customer_name})
        print("Executed create_cart_sql")
        cart_id = connection.execute(get_cart_id_sql, {"customer_name": customer_name}).one()[0]
        print("Executed get_cart_id_sql")
    payload = {"cart_id": cart_id}
    print(payload)
    return payload


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    """ """
    print("calling get_cart with cart_id:", cart_id)
    get_cart_sql = sqlalchemy.text("select * from global_carts where cart_id = {}".format(cart_id))
    print("get_cart_sql:", get_cart_sql)
    with db.engine.begin() as connection:
        try:
            result = connection.execute(get_cart_sql).one()
        except sqlalchemy.exc.NoResultFound:
            raise HTTPException(status_code=404, detail="Item not found")
    payload = {"customer": result[1]}
    print(payload)

    return payload


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    """ """
    print("Calling set_item_quantity:", "cart_id:", cart_id, "item_sku:", item_sku, "cart_item:", cart_item)

    # check if item is already in cart
    get_item_sql = sqlalchemy.text(
        "select * from global_cart_items where cart_id = :cart_id and sku = :sku"
    )
    print("get_item_sql:", get_item_sql)
    # update catalog quantity
    update_catalog_sql = sqlalchemy.text(
        "update global_catalog set quantity = quantity - :quantity where sku = :sku"
    )
    with db.engine.begin() as connection:
        connection.execute(update_catalog_sql, {"quantity": cart_item.quantity, "sku": item_sku})
        print("Executed update_catalog_sql")
        result = connection.execute(get_item_sql, {"cart_id": cart_id, "sku": item_sku}).fetchall()
        print("Executed get_item_sql")
        if len(result) == 0:
            # add item to cart
            add_item_sql = sqlalchemy.text(
                "insert into global_cart_items(cart_id, sku, quantity, price) values(:cart_id, :sku, :quantity, 50 * :quantity)"
            )
            print("add_item_sql:", add_item_sql)
            connection.execute(
                add_item_sql,
                {"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity},
            )
            print("Executed add_item_sql")
        else:
            # update item in cart
            update_item_sql = sqlalchemy.text(
                "update global_cart_items set \
                quantity = quantity + :quantity, \
                price = price + 50 \
                where cart_id = :cart_id and sku = :sku"
            )
            print("update_item_sql:", update_item_sql)
            connection.execute(
                update_item_sql,
                {"cart_id": cart_id, "sku": item_sku, "quantity": cart_item.quantity},
            )
            print("Executed update_item_sql")
        # check if needed to clear catalog row
        get_catalog_quantity_sql = sqlalchemy.text(
            "select quantity from global_catalog where sku = :sku"
        )
        print("get_catalog_quantity_sql:", get_catalog_quantity_sql)
        catalog_quantity = connection.execute(get_catalog_quantity_sql, {"sku": item_sku}).one()[0]
        print("Executed get_catalog_quantity_sql")
        if catalog_quantity == 0:
            delete_catalog_sql = sqlalchemy.text("delete from global_catalog where sku = :sku")
            print("delete_catalog_sql:", delete_catalog_sql)
            connection.execute(delete_catalog_sql, {"sku": item_sku})
            print("Executed delete_catalog_sql")
    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    """ """
    cart = get_cart(cart_id)
    potions_bought = 0
    gold_paid = 0
    print("Calling checkout:", "cart_id:", cart_id, "cart_checkout:", cart_checkout)
    get_items_sql = sqlalchemy.text("select * from global_cart_items where cart_id = :cart_id")
    print("get_items_sql:", get_items_sql)
    with db.engine.begin() as connection:
        result = connection.execute(get_items_sql, {"cart_id": cart_id}).fetchall()
        print("Executed get_items_sql")
        if len(result) == 0:
            raise HTTPException(status_code=404, detail="Cart not found")
        for row in result:
            quantity = row[2]
            price = row[3]
            sku = row[4]
            potions_bought += quantity
            gold_paid += price
            print("Current item, sku, quantity, price:", row, sku, quantity, price)
            # delete item from cart
            delete_item_sql = sqlalchemy.text(
                "delete from global_cart_items where cart_id = :cart_id and sku = :sku"
            )
            print("delete_item_sql:", delete_item_sql)
            connection.execute(delete_item_sql, {"cart_id": cart_id, "sku": sku})
            print("Executed delete_item_sql")
            # add order to order_history
            add_order_sql = sqlalchemy.text(
                "insert into order_history(customer_name, potion_sku, quantity, checkout_time, price, payment) \
                values(:customer_name, :potion_sku, :quantity, now(), :price, :payment)"
            )
            print("add_order_sql:", add_order_sql)
            connection.execute(
                add_order_sql,
                {"customer_name": cart['customer'], "potion_sku": sku, "quantity": quantity, "price": price,
                 "payment": cart_checkout.payment},
            )
            print("Executed add_order_sql")
        # update inventory
        update_inventory_sql = sqlalchemy.text(
            "update global_inventory set checking_gold = checking_gold + :gold_paid"
        )
        print("update_inventory_sql:", update_inventory_sql)
        connection.execute(update_inventory_sql, {"gold_paid": gold_paid})
        print("Executed update_inventory_sql")
        # delete cart
        delete_cart_sql = sqlalchemy.text("delete from global_carts where cart_id = :cart_id")
        print("delete_cart_sql:", delete_cart_sql)
        connection.execute(delete_cart_sql, {"cart_id": cart_id})

    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}
