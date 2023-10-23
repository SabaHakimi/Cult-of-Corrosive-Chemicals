import sqlalchemy
from src import database as db
from fastapi import HTTPException

def get_shop_gold(connection):
    return connection.execute(sqlalchemy.text("""
        SELECT COALESCE(SUM(change), 0)
        FROM gold_ledger
    """)).scalar_one()

def get_liquids_data(connection):
    return [x._asdict() for x in connection.execute(sqlalchemy.text("""
        SELECT liquid_type, COALESCE(SUM(change), 0) as quantity
        FROM liquids_ledger
        GROUP BY liquid_type
    """)).all()]

def get_potions_data(connection):
    return [x._asdict() for x in connection.execute(sqlalchemy.text("""
        SELECT potion_sku, COALESCE(SUM(change), 0) as quantity
        FROM potions_ledger
        GROUP BY potion_sku
    """)).all()]

def log_shop_data(connection):
    # Log liquids data
    liquids_data = get_liquids_data(connection)
    print(f"\nCurrent liquids inventory:")
    for item in liquids_data:
        print(f"type: {item['liquid_type']}, quantity: {item['quantity']}")
    
    # Log potions data
    potions_data = get_potions_data(connection)
    print(f"\nCurrent potions inventory:")
    for item in potions_data:
        print(f"type: {item['potion_sku']}, quantity: {item['quantity']}")
    
    # Log gold
    gold = get_shop_gold(connection)
    print(f"\nCurrent gold: {gold}\n")

def get_cart_data(connection, cart_id):
    return connection.execute(sqlalchemy.text("SELECT customer_name, payment, timestamp FROM carts WHERE id = :id"), [{"id": cart_id}]).first()
