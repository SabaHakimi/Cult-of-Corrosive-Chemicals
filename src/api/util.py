import sqlalchemy
from src import database as db

def get_shop_data(connection):
    qry_sql = """SELECT num_red_potions, num_red_ml, num_green_potions, num_green_ml, num_blue_potions, num_blue_ml, gold FROM global_inventory"""    
    result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()
    print(f"num_red_potions: {data.num_red_potions}, num_red_ml: {data.num_red_ml},"
          f"\nnum_green_potions: {data.num_green_potions}, num_green_ml: {data.num_green_ml},"
          f"\nnum_blue_potions: {data.num_blue_potions}, num_blue_ml: {data.num_blue_ml}," 
          f"\ngold: {data.gold}\n")

    return data

def get_cart_data(connection, cart_id):
    qry_sql = f"""SELECT customer_name, red_potion_0 FROM carts WHERE id = {cart_id}"""
    result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    return data