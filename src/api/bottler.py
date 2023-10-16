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
        print("\nPre-mix:")
        util.log_shop_data(connection)

        # Mix all potions and expend ml appropriately
        print("\nMixing:")
        for i in range(len(potions_delivered)):
            num_potions_made = potions_delivered[i].quantity
            print(f"{num_potions_made} potions of type {potions_delivered[i].potion_type} made")

            connection.execute(sqlalchemy.text("""UPDATE potions
            SET quantity = quantity + :num_potions_made
            WHERE type = :potion_type"""), [{"num_potions_made": num_potions_made, "potion_type": potions_delivered[i].potion_type}])
            
            for j in range(len(potions_delivered[i].potion_type)):
                print(f"{potions_delivered[i].potion_type[j]} ml of liquid {j + 1} expended")
                connection.execute(sqlalchemy.text("""UPDATE liquids
                SET quantity = quantity - :num_ml_expended
                WHERE id = :liquid"""), [{"num_ml_expended": potions_delivered[i].potion_type[j] * potions_delivered[i].quantity, "liquid": j + 1}])
            print("\n")

        print("\nPost-mix:")
        util.log_shop_data(connection)

        # Error catching
        data = util.get_liquids_data(connection)
        for item in data:
            if item.quantity < 0:
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
    # Initialize Variables
    potion_plan = []

    # Main Logic
    print("\nCalling get_bottle_plan")
    with db.engine.begin() as connection:
        # Pull data from DB and log
        util.log_shop_data(connection)

        red_ml = connection.execute(sqlalchemy.text("""SELECT quantity FROM liquids WHERE type = :type"""), [{"type": [100,0,0,0]}]).scalar_one()
        green_ml = connection.execute(sqlalchemy.text("""SELECT quantity FROM liquids WHERE type = :type"""), [{"type": [0,100,0,0]}]).scalar_one()
        blue_ml = connection.execute(sqlalchemy.text("""SELECT quantity FROM liquids WHERE type = :type"""), [{"type": [0,0,100,0]}]).scalar_one()

        potions = util.get_potions_data(connection)
        num_potions = 0
        for potion in potions:
            num_potions += potion.quantity
        print(f"\nnum_total_potions: {num_potions}")

        # Determine mixable amount of liquid
        total_ml = red_ml + green_ml + blue_ml
        total_potion_cnt_after_mix = (total_ml // 100) + num_potions
        ml_over_capacity = (total_potion_cnt_after_mix - 300) * 100

        if ml_over_capacity > 0:
            red_ml -= ml_over_capacity // 3
            green_ml -= ml_over_capacity // 3
            blue_ml -= ml_over_capacity // 3

        # Mixing
        potion_plan = []
        if red_ml >= 600 and green_ml >= 600 and blue_ml >= 600:
            potions = util.get_potions_data(connection)
            num_to_mix_per_type = min(red_ml // 200, green_ml // 200, blue_ml // 200)
            print(f"num_to_mix_per_type: {num_to_mix_per_type}")
            for potion in potions:
                potion_plan.append(
                    {
                        "potion_type": potion.type,
                        "quantity": num_to_mix_per_type
                    }
                )
        else:
            liquids = util.get_liquids_data(connection)
            for liquid in liquids:
                if liquid.quantity >= 100:
                    potion_plan.append(
                        {
                            "potion_type": liquid.type,
                            "quantity": min(5, liquid.quantity // 100)
                        }
                    )

        # Logging
        print("\nPotion plan:")
        for potion in potion_plan:
            print(potion)

        return potion_plan
