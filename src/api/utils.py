from sqlalchemy import func
from sqlalchemy.orm import sessionmaker, Session


# ... (assuming engine and Session are already set up)

def get_total_red_ml(seller_id):
    session = Session()  # Create a new session

    # Perform the query
    total_red_ml = (
        session.query(func.sum(InventoryLedgerEntry.red_ml_change).label('total_red_ml'))
        .filter(InventoryLedgerEntry.seller == seller_id)
        .scalar()  # This gets the actual value
    )

    session.close()  # Close the session

    return total_red_ml or 0  # func.sum() returns None if no rows are found. We're defaulting to 0 in that case.

def get_checking_gold_balance(seller_id):
    session = Session()  # Create a new session

    # Perform the query
    checking_gold_balance = (
        session.query(func.sum(GoldLedgerEntry.checking_gold_change).label('checking_gold_balance'))
        .filter(GoldLedgerEntry.seller == seller_id)
        .scalar()  # This gets the actual value
    )

    session.close()  # Close the session

    return checking_gold_balance or 0  # func.sum() returns None if no rows are found. We're defaulting to 0 in that case.
