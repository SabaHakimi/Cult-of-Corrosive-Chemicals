import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
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
    print("Calling create_cart")
    with db.engine.begin() as connection:
        set_sql = f"""INSERT INTO carts (customer_name) VALUES ('{new_cart.customer}') RETURNING id"""
        result = connection.execute(sqlalchemy.text(set_sql))
        cart_id = result.first()

        cart_data = util.get_cart_data(connection, cart_id.id)
        print(f"Created cart for {cart_data.customer_name}")

        return {"cart_id": cart_id.id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    print("Calling get_cart")
    with db.engine.begin() as connection:
        qry_sql = f"""SELECT id, customer_name, red_potion_0, payment FROM carts WHERE id = {cart_id}"""
        result = connection.execute(sqlalchemy.text(qry_sql))
        data = result.first()
        
        return data._asdict()


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    print("Calling set_item_quantity")
    with db.engine.begin() as connection:
        shop_data = util.get_shop_data(connection)
        if shop_data.num_red_potions < cart_item.quantity:
            print("Cannot fulfill order")
            raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.")
        
        set_sql = f"""UPDATE carts SET {item_sku} = {cart_item.quantity} WHERE id = {cart_id}"""
        connection.execute(sqlalchemy.text(set_sql))
        cart_entry = util.get_cart_data(connection, cart_id)
        print(f"Cart {cart_id} for {cart_entry.customer_name} requests {cart_entry.red_potion_0} potions")

        return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    print("Calling checkout")
    with db.engine.begin() as connection:
        shop_data = util.get_shop_data(connection)
        cart_data = util.get_cart_data(connection, cart_id)
        potions_sold = cart_data.red_potion_0
        gold_earned = 50 * cart_data.red_potion_0
        print(f"num_red_potions requested in cart: {cart_data.red_potion_0}")

        if shop_data.num_red_potions < cart_data.red_potion_0:
            print("Cannot fulfill order")
            raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.") 
        
        set_transaction_sql = f"""UPDATE global_inventory SET 
        num_red_potions = num_red_potions - {potions_sold}, gold = gold + {gold_earned}"""
        connection.execute(sqlalchemy.text(set_transaction_sql))

        print("Transaction completed:")
        util.get_shop_data(connection)

        store_payment_sql = f"""UPDATE carts SET payment = '{cart_checkout.payment}' WHERE id = {cart_id}"""
        connection.execute(sqlalchemy.text(store_payment_sql))
        # delete_cart_sql = """DELETE FROM carts WHERE id = {}""".format(cart_id)

        return {"total_potions_bought": potions_sold, "total_gold_paid": gold_earned}
