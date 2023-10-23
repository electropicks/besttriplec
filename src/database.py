

import os

import dotenv
from sqlalchemy import (create_engine, MetaData, Table, Column, BigInteger, Integer, Text,
                        CheckConstraint, String, TIMESTAMP)
from sqlalchemy.schema import ForeignKeyConstraint


def database_connection_url():
    dotenv.load_dotenv()

    return os.environ.get("POSTGRES_URI")


engine = create_engine(database_connection_url(), pool_pre_ping=True)

metadata = MetaData()

global_cart_items = Table('global_cart_items', metadata,
                          Column('item_id', BigInteger, primary_key=True),
                          Column('cart_id', BigInteger, nullable=False),
                          Column('quantity', Integer, nullable=False, server_default='0'),
                          Column('price', Integer, nullable=False, server_default='0'),
                          Column('sku', Text, nullable=False),
                          ForeignKeyConstraint(['cart_id'], ['global_carts.cart_id'], onupdate='CASCADE',
                                               ondelete='CASCADE'),
                          # If 'item_id' isn't auto-incremented by default, you'll need to set it explicitly
                          # depending on your database's dialect
                          )

global_catalog = Table('global_catalog', metadata,
                       Column('potion_id', BigInteger, primary_key=True),
                       Column('red_ml', Integer, nullable=False),
                       Column('green_ml', Integer, nullable=False),
                       Column('blue_ml', Integer, nullable=False),
                       Column('dark_ml', Integer, nullable=False),
                       Column('quantity', Integer, nullable=False),
                       Column('sku', Text, nullable=False),
                       )

global_inventory = Table('global_inventory', metadata,
                         Column('seller', String, primary_key=True, server_default='besttriplec'),
                         Column('red_ml', Integer, nullable=False, server_default='0'),
                         Column('green_ml', Integer, nullable=False, server_default='0'),
                         Column('blue_ml', Integer, nullable=False, server_default='0'),
                         Column('dark_ml', Integer, nullable=False, server_default='0'),
                         Column('checking_gold', Integer, nullable=False, server_default='100'),
                         Column('saving_gold', Integer, nullable=False, server_default='0'),
                         CheckConstraint('checking_gold >= 0', name='global_inventory_checking_gold_check'),
                         CheckConstraint('dark_ml >= 0', name='global_inventory_dark_ml_check'),
                         CheckConstraint('blue_ml >= 0', name='global_inventory_blue_ml_check'),
                         CheckConstraint('red_ml >= 0', name='global_inventory_red_ml_check'),
                         CheckConstraint('saving_gold >= 0', name='global_inventory_saving_gold_check'),
                         CheckConstraint('green_ml >= 0', name='global_inventory_green_ml_check'),
                         )

order_history = Table('order_history', metadata,
                      Column('order_id', BigInteger, primary_key=True),
                      Column('customer_name', Text, nullable=False),
                      Column('potion_sku', Text, nullable=False),
                      Column('quantity', Integer, nullable=False, server_default='0'),
                      Column('checkout_time', TIMESTAMP, nullable=False),
                      Column('price', Integer, nullable=False),
                      Column('payment', Text),
                      )
