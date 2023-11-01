from datetime import datetime
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import asc, desc
from sqlalchemy.orm import Session

from src.api import auth
from src.database import GlobalCatalog, OrderHistory, GlobalInventory, GlobalCarts, get_db, ProfessorCalls

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


class Order(BaseModel):
    order_id: int
    potion_sku: str
    customer_name: str
    price: int
    checkout_time: datetime

    def __str__(self):
        return f"Order({self.order_id}, {self.potion_sku}, {self.customer_name}, {self.price}, {self.checkout_time})"

    def __repr__(self):
        return self.__str__()


@router.get("/search/", tags=["search"])
def search_orders(
        customer_name: str = "",
        item_sku: str = "",
        search_page: int = 1,
        sort_col: search_sort_options = search_sort_options.timestamp,
        sort_order: search_sort_order = search_sort_order.desc,
        db: Session = Depends(get_db)
):
    # Define the sorting direction
    if sort_order == search_sort_order.asc:
        order_direction = asc
    else:
        order_direction = desc

    # Query the database
    orders_query = db.query(OrderHistory)
    if customer_name:
        print("applying customer_name filter")
        orders_query = orders_query.filter(OrderHistory.customer_name.ilike(f"%{customer_name}%"))
    if item_sku:
        print("applying item_sku filter")
        orders_query = orders_query.filter(OrderHistory.potion_sku.ilike(f"%{item_sku}%"))

    # Apply sorting
    orders_query = orders_query.order_by(order_direction(getattr(OrderHistory, translateTerms(sort_col.value))))

    # Implement pagination
    PAGE_SIZE = 5
    offset = (search_page - 1) * PAGE_SIZE
    orders = orders_query.limit(PAGE_SIZE).offset(offset).all()

    # Determine if there are previous or next pages
    previous_page = search_page - 1 if search_page > 1 else None
    next_page = search_page + 1 if len(orders) == PAGE_SIZE + 1 else None

    # Format the results
    results = [{"order_id": order.order_id,
                "item_sku": order.potion_sku,
                "customer_name": order.customer_name,
                "line_item_total": order.price,
                "timestamp": order.checkout_time.isoformat()} for order in orders]

    return {
        "previous": previous_page,
        "next": next_page,
        "results": results
    }


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart, db: Session = Depends(get_db)):
    prof_call = ProfessorCalls(
        endpoint="carts/",
        arguments={
            "new_cart": new_cart
        }
    )
    db.add(prof_call)
    db.flush()
    cart = GlobalCarts(customer_name=new_cart.customer, created_at=datetime.utcnow())
    db.add(cart)
    db.commit()
    db.refresh(cart)
    print("Created cart: ", cart.cart_id)
    return {"cart_id": cart.cart_id}


@router.get("/{cart_id}")
def get_cart(cart_id: int, db: Session = Depends(get_db)):
    prof_call = ProfessorCalls(
        endpoint="carts/{cart_id}",
        arguments={
            "cart_id": cart_id
        }
    )
    db.add(prof_call)
    db.commit()
    cart = db.query(GlobalCarts).filter_by(cart_id=cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"customer": cart.customer_name}


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem, db: Session = Depends(get_db)):
    """ """
    prof_call = ProfessorCalls(
        endpoint="carts/{cart_id}/items/{item_sku}",
        arguments={
            "cart_id": cart_id,
            "item_sku": item_sku,
            "cart_item": cart_item
        }
    )
    db.add(prof_call)
    db.flush()

    cart_items = db.query(CartItem).filter_by(cart_id=cart_id, sku=item_sku).all()
    catalog_item = db.query(GlobalCatalog).filter_by(sku=item_sku).first()

    if not catalog_item:
        raise HTTPException(status_code=404, detail="Catalog item not found")

    # Update catalog quantity
    catalog_item.quantity -= cart_item.quantity

    if len(cart_items) == 0:
        # Add item to cart
        new_cart_item = CartItem(cart_id=cart_id, sku=item_sku, quantity=cart_item.quantity,
                                 price=50 * cart_item.quantity)
        db.add(new_cart_item)
    else:
        # Update item in cart
        for item in cart_items:
            item.quantity += cart_item.quantity
            item.price += 50 * cart_item.quantity

    # Remove catalog item if quantity is zero
    if catalog_item.quantity == 0:
        db.delete(catalog_item)

    db.commit()

    return "OK"


class CartCheckout(BaseModel):
    payment: str


@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout, db: Session = Depends(get_db)):
    """ """
    prof_call = ProfessorCalls(
        endpoint="carts/{cart_id}/checkout",
        arguments={
            "cart_id": cart_id,
            "cart_checkout": cart_checkout
        }
    )
    db.add(prof_call)
    db.flush()

    cart = db.query(GlobalCarts).filter_by(id=cart_id).first()
    if not cart:
        raise HTTPException(status_code=404, detail="Cart not found")

    cart_items = db.query(CartItem).filter_by(cart_id=cart_id).all()

    potions_bought = 0
    gold_paid = 0

    for item in cart_items:
        # Add order to order history
        new_order = OrderHistory(customer_name=cart.customer_name, potion_sku=item.sku, quantity=item.quantity,
                                 checkout_time=datetime.utcnow(), price=item.price, payment=cart_checkout.payment)
        db.add(new_order)

        potions_bought += item.quantity
        gold_paid += item.price

        # Update inventory
        inventory_item = db.query(GlobalInventory).first()
        if inventory_item:
            inventory_item.checking_gold += gold_paid

        # Delete item from cart
        db.delete(item)

    # Delete the cart
    db.delete(cart)

    db.commit()

    return {"total_potions_bought": potions_bought, "total_gold_paid": gold_paid}


def translateTerms(sort_col: str):
    if sort_col == "customer_name":
        return "customer_name"
    if sort_col == "item_sku":
        return "potion_sku"
    if sort_col == "line_item_total":
        return "price"
    return "checkout_time"
