

import os

import dotenv
from sqlalchemy import (create_engine)
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import sessionmaker


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")


engine = create_engine(database_connection_url(), pool_pre_ping=True)

# Reflect the existing database
Base = automap_base()
Base.prepare(engine, reflect=True)

# Create a session-maker
SessionLocal = sessionmaker(bind=engine)

print(Base.classes.keys())
# For example, if you have a 'user' table, you can access it as:
GoldLedgerEntries = Base.classes.gold_ledger_entries
GlobalCarts = Base.classes.global_carts
GlobalCartItems = Base.classes.global_cart_items
GlobalInventory = Base.classes.global_inventory
OrderHistory = Base.classes.order_history
