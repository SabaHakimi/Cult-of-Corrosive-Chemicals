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
        cart_id = connection.execute(sqlalchemy.text("""
            INSERT INTO carts (customer_name) 
            VALUES (:customer_name) 
            RETURNING id
        """), 
        [{"customer_name": new_cart.customer}]).first()

        cart_data = util.get_cart_data(connection, cart_id.id)
        print(f"\nCreated cart for {cart_data.customer_name} at {cart_data.timestamp}\n")

        return {"cart_id": cart_id.id}


@router.get("/{cart_id}")
def get_cart(cart_id: int):
    # Main Logic
    print("Calling get_cart")
    with db.engine.begin() as connection:
        return connection.execute(sqlalchemy.text("SELECT id, customer_name, payment, timestamp FROM carts WHERE id = :id"), [{"id": cart_id}]).first()._asdict()


class CartItem(BaseModel):
    quantity: int


@router.post("/{cart_id}/items/{item_sku}")
def set_item_quantity(cart_id: int, item_sku: str, cart_item: CartItem):
    print("\nCalling set_item_quantity")
    with db.engine.begin() as connection:
        # Logging and get data from DB
        util.log_shop_data(connection)
        
        # Verify that requested items are in stock
        num_in_inventory = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(change), 0)
            FROM potions_ledger 
            WHERE potion_sku = :item_sku"""), 
            [{"item_sku": item_sku}]).scalar_one()
        if num_in_inventory < cart_item.quantity:
            print("Cannot fulfill order")
            raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.")
        
        # Add items to cart
        connection.execute(sqlalchemy.text("""
            INSERT INTO cart_items (cart_fkey, potions_fkey, quantity)
            VALUES (:cart_fkey, (SELECT sku FROM potions WHERE sku = :item_sku), :quantity)
        """), 
        [{"cart_fkey": cart_id, 
          "item_sku": item_sku, 
          "quantity": cart_item.quantity}])
        
        cart_entry = util.get_cart_data(connection, cart_id)
        print(f"Cart {cart_id} for {cart_entry.customer_name} requests {cart_item.quantity} {item_sku}(s)\n")

        return "OK"


class CartCheckout(BaseModel):
    payment: str

@router.post("/{cart_id}/checkout")
def checkout(cart_id: int, cart_checkout: CartCheckout):
    print("\nCalling checkout")
    with db.engine.begin() as connection:
        # Log inventory and initialize variables
        print("\nPre-checkout:")
        util.log_shop_data(connection)
     
        total_potions_sold = 0
        total_gold_earned = 0
        gold_sql_statements = []
        gold_sql_statement_args = []
        potion_sql_statements = []
        potion_sql_statement_args = []

        items_in_cart = connection.execute(sqlalchemy.text("""
            SELECT cart_items.potions_fkey, cart_items.quantity, COALESCE(SUM(potions_ledger.change), 0) AS num_in_inventory
            FROM cart_items
            LEFT JOIN potions_ledger ON cart_items.potions_fkey = potions_ledger.potion_sku
            WHERE cart_items.cart_fkey = :cart_id
            GROUP BY cart_items.potions_fkey, cart_items.quantity
        """), [{"cart_id": cart_id}])

        for item in items_in_cart:
            # Verify that requested items are in stock
            if item.num_in_inventory < item.quantity:
                print("Cannot fulfill order")
                raise HTTPException(status_code=400, detail="Not enough potions to fulfill order.")
            
            print(f"Selling {item.quantity} {item.potions_fkey}s for {item.quantity * 50} gold")

            transaction_id = connection.execute(sqlalchemy.text("""
                INSERT INTO transactions (description)
                VALUES ('Cart checkout')
                RETURNING id
            """)).first().id

            gold_sql_statements.append("""
                INSERT INTO gold_ledger (transaction_id, change)
                VALUES (:transaction_id, :change)
            """)
            gold_sql_statement_args.append([{
                "transaction_id": transaction_id,
                "change": item.quantity * 50
            }])

            potion_sql_statements.append("""
                INSERT INTO potions_ledger (transaction_id, potion_sku, change)
                VALUES (:transaction_id, :potion_sku, :change)
            """)
            potion_sql_statement_args.append([{
              "transaction_id": transaction_id, 
              "potion_sku": item.potions_fkey, 
              "change": item.quantity * -1}])
            
            total_potions_sold += item.quantity
            total_gold_earned += item.quantity * 50
        
        # Execute statements
        for i in range(len(gold_sql_statements)):
            connection.execute(sqlalchemy.text(gold_sql_statements[i]), gold_sql_statement_args[i])
            connection.execute(sqlalchemy.text(potion_sql_statements[i]), potion_sql_statement_args[i])

        # Logging  
        print("\nTransaction completed.")
        util.log_shop_data(connection)

        # Enter payment
        connection.execute(sqlalchemy.text("""
            UPDATE carts 
            SET payment = :payment 
            WHERE id = :id
        """), 
        [{"payment": cart_checkout.payment, 
          "id": cart_id}])

        print(f"\nTotal_potions_bought: {total_potions_sold}, Total_gold_paid: {total_gold_earned}")
        return {"total_potions_bought": total_potions_sold, "total_gold_paid": total_gold_earned}
