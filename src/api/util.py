import sqlalchemy
from src import database as db

def get_shop_data():
    qry_sql = """SELECT num_red_potions, num_red_ml, gold FROM global_inventory"""    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    return data

def get_cart_data(cart_id):
    qry_sql = """SELECT customer_name, red_potion_0 FROM carts WHERE id = {}""".format(cart_id)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    return data