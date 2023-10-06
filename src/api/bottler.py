import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from enum import Enum
from pydantic import BaseModel
from src.api import auth
from src.api import util

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
    print("Calling post_deliver_bottles")
    print("potions_delivered:\n{}".format(potions_delivered))
    data = util.get_shop_data()

    num_red_ml_expended = potions_delivered[0].quantity * 100
    num_potions_made = potions_delivered[0].quantity
    print("num_red_ml_expended: {}\nnum_potions_made: {}".format(num_red_ml_expended, num_potions_made))
    set_sql = """UPDATE global_inventory SET num_red_ml = {}, 
    num_red_potions = {}""".format(data.num_red_ml - num_red_ml_expended, 
                            data.num_red_potions + num_potions_made)
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
    print("Calling get_bottle_plan")

    data = util.get_shop_data
    print("Pre-mix num_red_ml: {}".format(data.num_red_ml))
    print("Intending to make {} potions".format(data.num_red_ml // 100))
    if data.num_red_ml >= 100:
        return [
                {
                    "potion_type": [100, 0, 0, 0],
                    "quantity": data.num_red_ml // 100,
                }
        ]
    return []
