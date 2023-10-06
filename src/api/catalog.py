import sqlalchemy
from src import database as db
from fastapi import APIRouter
from src.api import util

router = APIRouter()

# This is what you have for sale
@router.get("/catalog/", tags=["catalog"])
def get_catalog():
    """
    Each unique item combination must have only a single price.
    """
    # Can return a max of 20 items.
    data = util.get_shop_data()

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
