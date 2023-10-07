import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
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
    print("Calling post_deliver_barrels")
    with db.engine.begin() as connection:
        print("Pre-barrel-delivery:")
        util.get_shop_data(connection)
        print(f"ml_added_from_barrel: {barrels_delivered[0].ml_per_barrel}, price: {barrels_delivered[0].price}")

        set_sql = f"""UPDATE global_inventory SET num_red_ml = num_red_ml + {barrels_delivered[0].ml_per_barrel}, 
        gold = gold - {barrels_delivered[0].price}"""
        connection.execute(sqlalchemy.text(set_sql))

        print("Post-barrel-delivery:")
        util.get_shop_data(connection)

        return "OK"

# Gets called once a day
# Place order
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print("Calling get_wholesale_purchase_plan")
    with db.engine.begin() as connection:
        data = util.get_shop_data(connection)    
        print("Wholesale Catalog:")
        for i in range(len(wholesale_catalog)):
            print(wholesale_catalog[i])
            if wholesale_catalog[i].sku == "SMALL_RED_BARREL":
                if data.num_red_potions < 10 and wholesale_catalog[i].price <= data.gold and wholesale_catalog[i].quantity > 0:
                    print(f"Planning to purchase {wholesale_catalog[i]}")
                    return [
                        {
                            "sku": wholesale_catalog[i].sku,
                            "quantity": 1
                        }
                    ]
        return []
