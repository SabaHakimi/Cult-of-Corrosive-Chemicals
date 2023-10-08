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
    # Initialize Variables
    catalog = []
    potion_mapping = {
        "red": [100, 0, 0, 0],
        "green": [0, 100, 0, 0],
        "blue": [0, 0, 100, 0]
    }
    # Can return a max of 20 items.
    # Main Logic
    with db.engine.begin() as connection:
        print("\nInventory:")
        data = util.get_shop_data(connection)

        # Add each potion type to the cart, if available
        for potion_color, potion_type in potion_mapping.items():
            num_potions = getattr(data, f'num_{potion_color}_potions')
            if num_potions > 0:
                catalog_entry = {
                            "sku": f"{potion_color.upper()}_POTION",
                            "name": f"{potion_color} potion",
                            "quantity": num_potions,
                            "price": 50,
                            "potion_type": potion_type,
                        }
                catalog.append(catalog_entry)

        # Logging
        print("Catalog:")
        for item in catalog:
            print(item)
        print("\n")

        return catalog
