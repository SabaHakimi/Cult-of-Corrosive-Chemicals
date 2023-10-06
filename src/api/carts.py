import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from src.api import auth
from util import get_shop_data, get_cart_data

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
    set_sql = """INSERT INTO carts (customer_name) VALUES ('{}') RETURNING id""".format(new_cart.customer)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(set_sql))
    data = result.first()

    cart_data = get_cart_data(data.id)
    print("Created cart for {}".format(cart_data.customer_name))

    return {"cart_id": data.id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    print("Calling get_cart")
    qry_sql = """SELECT id, customer_name, red_potion_0, payment FROM carts WHERE id = {}""".format(cart_id)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()
    
    return data._asdict()


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    print("Calling set_item_quantity")
    
    set_sql = """UPDATE carts SET {} = {} WHERE id = {}""".format(item_sku, cart_item.quantity, cart_id)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(set_sql))
    cart_entry = get_cart_data(cart_id)
    print("Cart {} for {} requests {} potions".format(cart_id, cart_entry.customer_name, cart_entry.red_potion_0))

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    print("Calling checkout")

    shop_data = get_shop_data
    cart_data = get_cart_data(cart_id)
    potions_sold = cart_data.red_potion_0
    gold_earned = 50 * cart_data.red_potion_0

    print("gold before transation: {}".format(shop_data.gold))
    print("num_red_potions in shop: {}\nnum_red_potions requested in cart: {}".format(
        shop_data.num_red_potions, cart_data.red_potion_0))
    if shop_data.num_red_potions < cart_data.red_potion_0:
        print("Cannot fulfill order")
        raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.") 
       
    set_transaction_sql = """UPDATE global_inventory SET num_red_potions = {},
    gold = {}""".format(shop_data.num_red_potions - potions_sold, shop_data.gold + gold_earned)
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(set_transaction_sql))

    shop_data = get_shop_data()
    print("Transaction completed:\nnum_potions_remaining: {}, gold_after_earnings: {}".format(
        shop_data.num_red_potions, shop_data.gold))
    
    store_payment_sql = """UPDATE carts SET payment = '{}' WHERE id = {}""".format(cart_checkout.payment, cart_id)
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(store_payment_sql))
    # delete_cart_sql = """DELETE FROM carts WHERE id = {}""".format(cart_id)

    return {"total_potions_bought": potions_sold, "total_gold_paid": gold_earned}
