import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends, HTTPException
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
    color: str
    potion_type: list[int]
    quantity: int

@router.post("/deliver")
def post_deliver_bottles(potions_delivered: list[PotionInventory]):
    # Main Logic
    print("\nCalling post_deliver_bottles")
    with db.engine.begin() as connection:
        print("\npotions_delivered:")
        for potion in potions_delivered:
            print(potion)
        print("\nPre-mix inventory:")
        util.get_shop_data(connection)

        # Mix all potions and expend ml appropriately
        print("Mixing:")
        for i in range(len(potions_delivered)):
            num_potions_made = potions_delivered[i].quantity
            num_ml_expended = num_potions_made * 100
            print(f"num_red_ml_expended: {num_ml_expended}\nnum_potions_made: {num_potions_made}")

            set_sql = f"""UPDATE global_inventory 
            SET num_{potions_delivered[i].color}_ml = num_{potions_delivered[i].color}_ml - {num_ml_expended}, 
            num_{potions_delivered[i].color}_potions = num_{potions_delivered[i].color}_potions + {num_potions_made}"""
            connection.execute(sqlalchemy.text(set_sql))

        print("\nPost-mix inventory:")
        data = util.get_shop_data(connection)
        
        # Error catching
        if data.num_red_ml < 0 or data.num_green_ml < 0 or data.num_blue_ml < 0:
            print("Mixed potions from nonexistent liquid...Probably not a good idea to create matter out of nothing.")
            raise HTTPException(status_code=400, detail="Spent more ml than is available.") 

        return "OK"

# Gets called 4 times a day
@router.post("/plan")
def get_bottle_plan():
    """
    Go from barrel to bottle.
    """
    # Each bottle has a quantity of what proportion of red, blue, and green potion to add.
    # Expressed in integers from 1 to 100 that must sum up to 100.
    # Initial logic: bottle all barrels into red potions.
    # Initialize Variables
    potion_plan = []

    # Main Logic
    print("Calling get_bottle_plan")
    with db.engine.begin() as connection:
        # Pull data from DB and determine how many of each potion can be created
        print("Pre-mix:")
        data = util.get_shop_data(connection)
        potion_recipes = [("red", data.num_red_ml, [100, 0, 0, 0]), ("green", data.num_green_ml, [0, 100, 0, 0]), ("blue", data.num_blue_ml, [0, 0, 100, 0])]
        for color, potion_ml, formula in potion_recipes:
            if potion_ml >= 100:
                potion_plan.append(
                    {
                        "color": color,
                        "potion_type": formula,
                        "quantity": potion_ml // 100
                    }
                )
    
        print(f"Potion plan: {potion_plan}")
        return potion_plan
