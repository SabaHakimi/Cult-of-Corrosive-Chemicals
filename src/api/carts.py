import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/carts",
    tags=["cart"],
    dependencies=[Depends(auth.get_api_key)],
)


class NewCart(BaseModel):
    customer: str


@router.post("/")
def create_cart(new_cart: NewCart):
    set_sql = """INSERT INTO carts (customer_name) VALUES ('{}') RETURNING id""".format(new_cart.customer)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(set_sql))
    data = result.first()

    return {"cart_id": data.id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    qry_sql = """SELECT * FROM carts WHERE id = {}""".format(cart_id)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()
    
    return data._asdict()


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    qry_sql = """SELECT num_red_potions FROM global_inventory"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    if data.num_red_potions < cart_item.quantity:
        return "Cannot fulfill order"
    
    set_sql = """UPDATE carts SET {} = {} WHERE  id = {}""".format(item_sku, cart_item.quantity, cart_id)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(set_sql))

    return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    print(cart_checkout.payment)
    qry_shop_sql = """SELECT num_red_potions, gold FROM global_inventory"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_shop_sql))
    shop_data = result.first()

    qry_cart_sql = """SELECT red_potion_0 FROM carts WHERE id = {}""".format(cart_id)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_cart_sql))
    cart_data = result.first()
    
    set_transaction_sql = """UPDATE global_inventory SET num_red_potions = {},
    gold = {}""".format(shop_data.num_red_potions - cart_data.red_potion_0, shop_data.gold + (50 * cart_data.red_potion_0))
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(set_transaction_sql))
    
    store_payment_sql = """UPDATE carts SET payment = '{}' WHERE id = {}""".format(cart_checkout.payment, cart_id)
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(store_payment_sql))
    # delete_cart_sql = """DELETE FROM carts WHERE id = {}""".format(cart_id)

    return {"total_potions_bought": cart_data.red_potion_0, "total_gold_paid": 50 * cart_data.red_potion_0}
