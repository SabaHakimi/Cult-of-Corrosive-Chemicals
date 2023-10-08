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
    print("Calling post_deliver_barrels")
    print(f"barrels_delivered:\n{barrels_delivered}")
    with db.engine.begin() as connection:
        print("Pre-barrel-delivery:")
        util.get_shop_data(connection)
        for i in range(len(barrels_delivered)):
            color = barrels_delivered[i].sku.split('_')[1]
            set_sql = f"""UPDATE global_inventory 
            SET num_{color}_ml = num_{color}_ml + {barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity}, 
            gold = gold - {barrels_delivered[i].price * barrels_delivered[i].quantity}"""
            connection.execute(sqlalchemy.text(set_sql))
            print(f"ml_added_from_barrel: {barrels_delivered[i].ml_per_barrel * barrels_delivered[i].quantity}, price: {barrels_delivered[i].price * barrels_delivered[i].quantity}")

        print("Post-barrel-delivery:")
        data = util.get_shop_data(connection)

        if data.gold >= 0:
            return "OK"  
        else:
            print("Uh-oh, time to declare bankruptcy.")
            raise HTTPException(status_code=400, detail="Spent more gold than is available.") 

# Gets called once every other tick
# Place order
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    # Initialize Variables
    medium_validation_set = {"MEDIUM_RED_BARREL", "MEDIUM_GREEN_BARREL", "MEDIUM_BLUE_BARREL"}
    small_validation_set = {"SMALL_RED_BARREL", "SMALL_GREEN_BARREL", "SMALL_BLUE_BARREL"}
    purchase_plan = []
    price_threshold = -1

    # Main Logic
    print("Calling get_wholesale_purchase_plan")
    with db.engine.begin() as connection:
        # Pull data from DB
        data = util.get_shop_data(connection)
        expendable_gold = data.gold
 
        print("Wholesale Catalog:")
        # Iterate through catalog and determine purchase plan
        for i in range(len(wholesale_catalog)):
            print(wholesale_catalog[i])
            # Determine price threshold (and whether to skip the item)
            if wholesale_catalog[i].sku in medium_validation_set: 
                price_threshold = 570
            elif wholesale_catalog[i].sku in small_validation_set:
                price_threshold = wholesale_catalog[i].price
            else:
                continue
            # Add item to purchase plan if it can be purchased
            if wholesale_catalog[i].quantity > 0 and expendable_gold >= price_threshold:
                print(f"Planning to purchase {wholesale_catalog[i]}")
                purchase_plan.append(
                    {
                        "sku": wholesale_catalog[i].sku,
                        "quantity": 1
                    })
                expendable_gold -= wholesale_catalog[i].price
                
        return purchase_plan
