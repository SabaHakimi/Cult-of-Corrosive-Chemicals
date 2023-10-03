import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth

router = APIRouter(
    prefix="/bottler",
    tags=["bottler"],
    dependencies=[Depends(auth.get_api_key)],
)

class PotionInventory(BaseModel):
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    qry_sql = """SELECT num_red_ml, num_red_potions FROM global_inventory"""    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    set_sql = """UPDATE global_inventory SET num_red_ml = {}, 
    num_red_potions = {}""".format(data.num_red_ml - potions_delivered[0].quantity * 100, 
                            data.num_red_potions + potions_delivered[0].quantity)
    with db.engine.begin() as connection:
        connection.execute(sqlalchemy.text(set_sql))

    return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """

    # Each bottle has a quantity of what proportion of red, blue, and
    # green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.

    # Initial logic: bottle all barrels into red potions.

    qry_sql = """SELECT num_red_ml FROM global_inventory"""
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    return [
            {
                "potion_type": [100, 0, 0, 0],
                "quantity": data.num_red_ml // 100,
            }
        ]
