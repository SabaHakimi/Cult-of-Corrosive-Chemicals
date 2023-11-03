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
        potions = util.get_potions_data(connection)

        # Add each potion type to the cart, if available
        for potion in potions:
            if potion['quantity'] > 0:
                # Calculate potion price
                potion_price = 50 - max(((potion['quantity'] - 30) // 2), 0)
                # Update price in potions table
                connection.execute(sqlalchemy.text("""
                    UPDATE potions
                    SET price = :price
                    WHERE sku = :sku
                """),
                [{"price": 1 if potion['potion_sku'] == 'teal_potion' else potion_price, 
                  "sku": potion['potion_sku']}])
                
                # Create catalog entry and add to catalog
                catalog_entry = {
                            "sku": potion['potion_sku'],
                            "name": potion['potion_sku'],
                            "quantity": potion['quantity'],
                            "price": 1 if potion['potion_sku'] == 'teal_potion' else potion_price,
                            "potion_type": potion['type'],
                        }
                catalog.append(catalog_entry)

        # Logging
        print("Catalog:")
        for item in catalog:
            print(item)
        print("\n")

        return catalog
