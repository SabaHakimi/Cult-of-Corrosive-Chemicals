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
        expendable_gold = util.get_shop_gold(connection)
        print(f"\ngold: {expendable_gold}")
        liquids_data = util.get_liquids_data(connection)
        ml_count = {
            "red": util.get_ml(liquids_data, "red"), 
            "green": util.get_ml(liquids_data, "green"), 
            "blue": util.get_ml(liquids_data, "blue"),
            "dark": util.get_ml(liquids_data, "dark")
        }
        print(ml_count["dark"])
        
        # Determine what size barrels to consider
        for color, amount in ml_count.items():
            print(f"color: {color}, amount: {amount}")
            if amount < 3000:
                small_validation_set.add(f"SMALL_{color.upper()}_BARREL")
            if amount < 15000:
                medium_validation_set.add(f"MEDIUM_{color.upper()}_BARREL")
            if amount < 90000:
                large_validation_set.add(f"LARGE_{color.upper()}_BARREL")
 
        print("\nWholesale Catalog:")
        # Iterate through catalog and determine purchase plan
        gold_at_start = expendable_gold
        sorted_catalog = sorted(wholesale_catalog, key=lambda x: x.ml_per_barrel, reverse=True)
        purchases_left = -1 if gold_at_start <= 4500 else 4
        for i in range(len(sorted_catalog)):
            print(sorted_catalog[i])
            if gold_at_start <= 4500:
                # Determine price threshold (and whether to skip the item)
                if sorted_catalog[i].sku in large_validation_set:
                    price_threshold = 1250
                elif sorted_catalog[i].sku in medium_validation_set: 
                    price_threshold = 570
                elif sorted_catalog[i].sku in small_validation_set:
                    price_threshold = sorted_catalog[i].price
                else:
                    continue
                purchase_amount = 1
            else:
                print("purchases left: ", purchases_left)
                # Check if all 4 purchases completed
                if purchases_left == 0:
                    break

                # Setup vars
                color = sorted_catalog[i].sku.split('_')[1].lower()
                color_ml = ml_count[color]
                limit_by_price = (gold_at_start // 4) // sorted_catalog[i].price
                if sorted_catalog[i].sku in large_validation_set:
                    limit_by_desire = (((100000 if color == "dark" else 90000) - color_ml) // sorted_catalog[i].ml_per_barrel) + 1
                elif sorted_catalog[i].sku in medium_validation_set:
                    limit_by_desire = ((15000 - color_ml) // sorted_catalog[i].ml_per_barrel) + 1
                else:
                    continue
                # Define purchase amount and mark purchase
                print(f"limit by price: {limit_by_price}, limit by desire: {limit_by_desire}")
                purchase_amount = min(sorted_catalog[i].quantity, limit_by_price, limit_by_desire) 
                price_threshold = sorted_catalog[i].price * purchase_amount
                purchases_left -= 1
            
            # Add item to purchase plan if it can be purchased
                if sorted_catalog[i].quantity > 0 and expendable_gold >= price_threshold and purchase_amount > 0:
                    purchase_plan.append(
                        {
                            "sku": sorted_catalog[i].sku,
                            "quantity": purchase_amount
                        })
                    expendable_gold -= sorted_catalog[i].price * purchase_amount
                elif gold_at_start > 4500:
                    print(f"Broke ah hell. You have {expendable_gold} and need {price_threshold}")

        print(f"\nPurchase plan: {purchase_plan}")  
        return purchase_plan
