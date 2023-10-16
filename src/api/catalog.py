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
    # Main Logic
    with db.engine.begin() as connection:
        print("\nInventory:")
        util.log_shop_data(connection)
        catalog = []
        potions_inventory = util.get_potions_data(connection)

        # Add each potion type to the cart, if available
        for potion in potions_inventory:
            if potion.quantity > 0:
                catalog_entry = {
                            "sku": potion.sku,
                            "name": potion.sku,
                            "quantity": potion.quantity,
                            "price": 50,
                            "potion_type": potion.type,
                        }
                catalog.append(catalog_entry)

        # Logging
        print("Catalog:")
        for item in catalog:
            print(item)
        print("\n")

        return catalog
