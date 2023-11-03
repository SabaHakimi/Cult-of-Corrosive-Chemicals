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
    print("\nCalling post_deliver_bottles")
    with db.engine.begin() as connection:
        # Logging 
        print("\npotions_delivered:")
        for potion in potions_delivered:
            print(potion)
        print("\nPre-mix:")
        util.log_shop_data(connection)

        # Mix all potions and expend ml appropriately
        print("\nMixing:")
        
        liquid_mapping = ["red", "green", "blue", "dark"]

        for i in range(len(potions_delivered)):
            num_potions_made = potions_delivered[i].quantity
            potion_type = potions_delivered[i].potion_type
            print(f"{num_potions_made} potions of type {potion_type} made")

            # Add new transaction
            transaction_id = connection.execute(sqlalchemy.text("""
                INSERT INTO transactions (description)
                VALUES ('Mixing potions')
                RETURNING id
            """)).first().id

            # Update potions ledger
            connection.execute(sqlalchemy.text("""
                INSERT INTO potions_ledger (transaction_id, potion_sku, change)
                VALUES (:transaction_id, (SELECT sku FROM potions WHERE type = :potion_type), :change)
            """),
            [{"transaction_id": transaction_id, 
              "potion_type": potion_type, 
              "change": num_potions_made}])
            
            # Update liquids ledger
            for j in range(len(potions_delivered[i].potion_type)):
                change = potions_delivered[i].potion_type[j] * potions_delivered[i].quantity
                print(f"{change} ml of {liquid_mapping[j]} liquid expended")
                if (change != 0):
                    connection.execute(sqlalchemy.text("""
                        INSERT INTO liquids_ledger (transaction_id, liquid_type, change)
                        VALUES (:transaction_id, :liquid_type, :change)
                    """),
                    [{"transaction_id": transaction_id, 
                    "liquid_type": liquid_mapping[j], 
                    "change": change * -1}])
            print("\n")

        print("\nPost-mix:")
        util.log_shop_data(connection)

        # Error catching
        data = util.get_liquids_data(connection)
        for item in data:
            if item['quantity'] < 0:
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

    print("\nCalling get_bottle_plan")
    with db.engine.begin() as connection:
        # Logging
        util.log_shop_data(connection)

        # Determine mixable amount of liquid
        num_potions = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(change), 0) as quantity
            FROM potions_ledger
        """)).scalar_one()
        print(f"num_total_potions: {num_potions}")

        total_ml = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(change), 0) as quantity
            FROM liquids_ledger
        """)).scalar_one()

        max_mix_count_per_type = (300 - num_potions) // 6

        # Mixing
        ml_data = util.get_liquids_data(connection)
        red_ml = util.get_ml(ml_data, "red")
        green_ml = util.get_ml(ml_data, "green")
        blue_ml = util.get_ml(ml_data, "blue")


        potion_plan = []
        mix_all = True
        
        if len(ml_data) < 3:
            mix_all = False
        else:
            if red_ml < 600 or green_ml < 600 or blue_ml < 450:
                mix_all = False

        if mix_all:
            potions = connection.execute(sqlalchemy.text("SELECT sku, type FROM potions"))
            num_to_mix_per_type = min(red_ml // 200, green_ml // 150, blue_ml // 150)
            num_to_mix_per_type = min(num_to_mix_per_type, max_mix_count_per_type)
            print(f"num_to_mix_per_type: {num_to_mix_per_type}")
            for potion in potions:
                if potion.sku != 'teal_potion':
                    potion_plan.append(
                        {
                            "potion_type": potion.type,
                            "quantity": num_to_mix_per_type
                        }
                    )
        else:
            liquids = util.get_liquids_data(connection)
            liquid_mapping = {
                "red": [100, 0, 0, 0],
                "green": [0, 100, 0, 0],
                "blue": [0, 0, 100, 0]
            }
            for liquid in liquids:
                if liquid['quantity'] >= 100:
                    potion_plan.append(
                        {
                            "potion_type": liquid_mapping[liquid['liquid_type']],
                            "quantity": min(5, liquid['quantity'] // 100)
                        }
                    )

        # Logging
        print("\nPotion plan:")
        for potion in potion_plan:
            print(potion)

        return potion_plan
