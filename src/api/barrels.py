import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.api import auth
from src.api import util

router = APIRouter(
    prefix="/barrels",
    tags=["barrels"],
    dependencies=[Depends(auth.get_api_key)],
)

class Barrel(BaseModel):
    sku: str

    ml_per_barrel: int
    potion_type: list[int]
    price: int

    quantity: int

# Receive list of purchased barrels and finalize transaction
@router.post("/deliver")
def post_deliver_barrels(barrels_delivered: list[Barrel]):
    # Main Logic
    print("\nCalling post_deliver_barrels")
    print(f"\nbarrels_delivered:\n{barrels_delivered}")
    with db.engine.begin() as connection:
        print("\nPre-barrel-delivery:")
        util.log_shop_data(connection)
        # Update shop inventory; exchange gold for each barrel bought
        print("Barrels mixed into inventory:")
        for i in range(len(barrels_delivered)):
            # Add new transaction
            transaction_id = connection.execute(sqlalchemy.text("""
                INSERT INTO transactions (description)
                VALUES ('Barrel Purchase')
                RETURNING id
            """)).first().id
            
            # Update liquids ledger
            added_quantity = barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity
            liquid_color = barrels_delivered[i].sku.split('_')[1].lower()
            connection.execute(sqlalchemy.text("""
                INSERT INTO liquids_ledger (transaction_id, liquid_type, change)
                VALUES (:transaction_id, :liquid_type, :change)
            """), 
            [{"transaction_id": transaction_id, 
              "liquid_type": liquid_color, 
              "change": added_quantity}])
            
            # Update gold ledger
            price = barrels_delivered[i].price * barrels_delivered[i].quantity * -1
            connection.execute(sqlalchemy.text("""
                INSERT INTO gold_ledger (transaction_id, change)
                VALUES (:transaction_id, :change)
            """), 
            [{"transaction_id": transaction_id,  
              "change": price}])
            
            print(f"type: {liquid_color}, ml_added_from_barrel: {added_quantity}")

        print("\nPost-barrel-delivery:")
        util.log_shop_data(connection)

        # Catch any silly errors in my logic
        if util.get_shop_gold(connection) >= 0:
            return "OK"  
        else:
            print("Uh-oh, time to declare bankruptcy.")
            raise HTTPException(status_code=400, detail="Spent more gold than is available.") 

# Gets called once every other tick
# Place order
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    # Initialize Variables
    large_validation_set = {"LARGE_DARK_BARREL"}
    medium_validation_set = {"MEDIUM_DARK_BARREL"}
    small_validation_set = {"SMALL_DARK_BARREL"}
    purchase_plan = []
    price_threshold = -1

    # Main Logic
    print("\nCalling get_wholesale_purchase_plan")
    with db.engine.begin() as connection:
        # Pull data from DB and log current values
        liquids_data = util.get_liquids_data(connection)
        red_ml = util.get_ml(liquids_data, "red")
        if red_ml < 20000:
            large_validation_set.add("LARGE_RED_BARREL")
            medium_validation_set.add("MEDIUM_RED_BARREL")
            small_validation_set.add("SMALL_RED_BARREL")
        green_ml = util.get_ml(liquids_data, "green")
        if green_ml < 20000:
            large_validation_set.add("LARGE_GREEN_BARREL")
            medium_validation_set.add("MEDIUM_GREEN_BARREL")
            small_validation_set.add("SMALL_GREEN_BARREL")
        blue_ml = util.get_ml(liquids_data, "blue")
        if blue_ml < 20000:
            large_validation_set.add("LARGE_BLUE_BARREL")
            medium_validation_set.add("MEDIUM_BLUE_BARREL")
            small_validation_set.add("SMALL_BLUE_BARREL")

        expendable_gold = util.get_shop_gold(connection)
        print(f"\ngold: {expendable_gold}")
 
        print("\nWholesale Catalog:")
        # Iterate through catalog and determine purchase plan
        for i in range(len(wholesale_catalog)):
            print(wholesale_catalog[i])
            # Determine price threshold (and whether to skip the item)
            if wholesale_catalog[i].sku in large_validation_set:
                price_threshold = 1250
            elif wholesale_catalog[i].sku in medium_validation_set: 
                price_threshold = 570
            elif wholesale_catalog[i].sku in small_validation_set:
                price_threshold = wholesale_catalog[i].price
            else:
                continue
            # Add item to purchase plan if it can be purchased
            if wholesale_catalog[i].quantity > 0 and expendable_gold >= price_threshold:
                purchase_plan.append(
                    {
                        "sku": wholesale_catalog[i].sku,
                        "quantity": 1
                    })
                expendable_gold -= wholesale_catalog[i].price

        print(f"\nPurchase plan: {purchase_plan}")      
        return purchase_plan
