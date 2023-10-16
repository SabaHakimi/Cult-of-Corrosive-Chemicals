import sqlalchemy
from src import database as db
from fastapi import HTTPException

def get_shop_gold(connection):
    return connection.execute(sqlalchemy.text("""SELECT gold FROM inventory""")).scalar_one()

def get_liquids_data(connection):
    return connection.execute(sqlalchemy.text(f"SELECT type, quantity FROM liquids"))
    
def get_potions_data(connection):
    return connection.execute(sqlalchemy.text(f"SELECT sku, type, quantity FROM potions"))

def log_shop_data(connection):
    liquids_data = get_liquids_data(connection)
    print(f"\nCurrent liquids inventory:")
    for item in liquids_data:
        print(f"type: {item.type}, quantity: {item.quantity},")
    potions_data = get_potions_data(connection)
    print(f"\nCurrent potions inventory:")
    for item in potions_data:
        print(f"sku: {item.sku}, type: {item.type}, quantity: {item.quantity},")
    gold = get_shop_gold(connection)
    print(f"\nCurrent gold: {gold}")

def get_cart_data(connection, cart_id):
    return connection.execute(sqlalchemy.text("SELECT customer_name, payment, timestamp FROM carts WHERE id = :id"), [{"id": cart_id}]).first()
