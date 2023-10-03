import sqlalchemy
from src import database as db

from fastapi import APIRouter

router = APIRouter()

# This is what you have for sale
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # Can return a max of 20 items.
    qry_sql = """SELECT num_red_potions FROM global_inventory"""    
    with db.engine.begin() as connection:
        result = connection.execute(sqlalchemy.text(qry_sql))
    data = result.first()

    if data.num_red_potions > 0:
        return [
                {
                    "sku": "RED_POTION_0",
                    "name": "red potion",
                    "quantity": data.num_red_potions,
                    "price": 50,
                    "potion_type": [100, 0, 0, 0],
                }
            ]
    return []
