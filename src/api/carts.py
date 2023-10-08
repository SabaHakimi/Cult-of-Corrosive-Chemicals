import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from src.api import auth
from src.api import util 

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    # Main Logic
    print("\nCalling create_cart")
    with db.engine.begin() as connection:
        set_sql = f"""INSERT INTO carts (customer_name, time) VALUES ('{new_cart.customer}', '{datetime.now().strftime("%d/%m/%Y %H:%M:%S")}') RETURNING id"""
        result = connection.execute(sqlalchemy.text(set_sql))
        cart_id = result.first()

        cart_data = util.get_cart_data(connection, cart_id.id)
        print(f"\nCreated cart for {cart_data.customer_name} at {cart_data.time}\n")

        return {"cart_id": cart_id.id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    # Main Logic
    print("Calling get_cart")
    with db.engine.begin() as connection:
        qry_sql = f"""SELECT id, customer_name, red_potion, green_potion, blue_potion, payment, time FROM carts WHERE id = {cart_id}"""
        result = connection.execute(sqlalchemy.text(qry_sql))
        data = result.first()
        
        return data._asdict()


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    # Main Logic
    print("\nCalling set_item_quantity")
    with db.engine.begin() as connection:
        # Logging and get data from DB
        print("\nCurrent shop inventory:")
        shop_data = util.get_shop_data(connection)
        
        # Verify that requested items are in stock
        if getattr(shop_data, f"num_{item_sku.lower()}s") < cart_item.quantity:
            print("Cannot fulfill order")
            raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.")
        
        # Add items to cart
        set_sql = f"""UPDATE carts SET {item_sku.lower()} = {cart_item.quantity} WHERE id = {cart_id}"""
        connection.execute(sqlalchemy.text(set_sql))
        cart_entry = util.get_cart_data(connection, cart_id)
        print(f"Cart {cart_id} for {cart_entry.customer_name} requests {cart_item.quantity} {item_sku}(s)\n")

        return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    # Main Logic
    print("\nCalling checkout")
    with db.engine.begin() as connection:
        # Get data and initialize variables
        print("\nPre-checkout shop inventory:")
        shop_data = util.get_shop_data(connection)
        cart_data = util.get_cart_data(connection, cart_id)
        colors = [("red", 50), ("green", 50), ("blue", 60)]
        total_potions_sold = 0
        total_gold_earned = 0
        sql_statements = []
        # print(f"num_red_potions requested in cart: {cart_data.red_potion_0}")

        for i in range(len(colors)):
            # Set values
            shop_potion = f"num_{colors[i][0]}_potions"
            cart_potion_quantity = getattr(cart_data, f"{colors[i][0]}_potion")
            gold_earned = colors[i][1] * cart_potion_quantity

            # Verify that requested items are in stock
            if getattr(shop_data, shop_potion) < cart_potion_quantity:
                print("Cannot fulfill order")
                raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.") 
            
            sql_statements.append(f"""UPDATE global_inventory 
            SET {shop_potion} = {shop_potion} - {cart_potion_quantity}, gold = gold + {gold_earned}""")
            total_potions_sold += cart_potion_quantity
            total_gold_earned += gold_earned
        
        # Execute statements
        for statement in sql_statements:
            connection.execute(sqlalchemy.text(statement))

        # Logging  
        print("Transaction completed. Shop inventory:")
        util.get_shop_data(connection)

        # Enter payment
        store_payment_sql = f"""UPDATE carts SET payment = '{cart_checkout.payment}' WHERE id = {cart_id}"""
        connection.execute(sqlalchemy.text(store_payment_sql))

        return {"total_potions_bought": total_potions_sold, "total_gold_paid": total_gold_earned}
