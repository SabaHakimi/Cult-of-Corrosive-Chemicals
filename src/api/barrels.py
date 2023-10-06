import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from util import get_shop_data

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
    data = get_shop_data()
    print("Pre-barrel-delivery:\nnum_red_ml: {}, gold: {}".format(data.num_red_ml, data.gold))
    print("ml_added_from_barrel: {}, price: {}".format(barrels_delivered[0].ml_per_barrel, barrels_delivered[0].price))

    set_sql = """UPDATE global_inventory SET num_red_ml = {}, 
    gold = {}""".format(data.num_red_ml + barrels_delivered[0].ml_per_barrel, 
                            data.gold - barrels_delivered[0].price)
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(set_sql))

    data = get_shop_data()
    print("Post-barrel-delivery:\nnum_red_ml: {}, gold: {}".format(data.num_red_ml, data.gold))

    return "OK"

# Gets called once a day
# Place order
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    print("Calling get_wholesale_purchase_plan")
    data = get_shop_data()
    print("Num_red_potions: {}, Gold: {}".format(data.num_red_potions, data.gold))
   
    print("Wholesale Catalog:")
    for i in range(len(wholesale_catalog)):
        print(wholesale_catalog[i])
        if wholesale_catalog[i].sku == "SMALL_RED_BARREL":
            if data.num_red_potions < 10 and wholesale_catalog[i].price <= data.gold and wholesale_catalog[i].quantity > 0:
                print ("Planning to purchase {}".format(wholesale_catalog[i]))
                return [
                    {
                        "sku": "SMALL_RED_BARREL",
                        "quantity": 1
                    }
                ]
    return []
