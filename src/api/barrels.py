import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth

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
    qry_sql = """SELECT num_red_ml, gold FROM global_inventory"""    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    set_sql = """UPDATE global_inventory SET num_red_ml = {}, 
    gold = {}""".format(data.num_red_ml + barrels_delivered[0].ml_per_barrel, 
                            data.gold - barrels_delivered[0].price)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(set_sql))

    return "OK"

# Gets called once a day
# Place order
@router.post("/plan")
def get_wholesale_purchase_plan(wholesale_catalog: list[Barrel]):
    sql_to_execute= """SELECT num_red_potions FROM global_inventory"""
    print(wholesale_catalog)
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(sql_to_execute))
    data = result.first()
    
    return [
        {
            "sku": "SMALL_RED_BARREL",
            "quantity": 1 if data.num_red_potions < 10 and 
            wholesale_catalog[0].price < data.gold and 
            wholesale_catalog[0].quantity > 0 else 0,
        }
    ]
