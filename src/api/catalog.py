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
        catalog_set = {"red_potion", "green_potion", "blue_potion", "dark_potion", "purple_potion", "brown_potion"}
        excluded_set = {"ocean_potion"}
        open_slots = 0

        # Add each potion type to the cart, if available
        for potion in potions:
            if potion['potion_sku'] in catalog_set and potion['quantity'] == 0:
                open_slots += 1
        for potion in potions:
            add_item = False
            if potion['potion_sku'] in catalog_set:
                add_item = True
            elif potion['potion_sku'] in excluded_set and open_slots > 0:
                add_item = True
                open_slots -= 1
            if add_item:
                if potion['quantity'] > 0:
                    # Calculate potion price
                    potion_price = 45 - max(min((potion['quantity'] - 30), 15), 0)
                    # Update price in potions table
                    connection.execute(sqlalchemy.text("""
                        UPDATE potions
                        SET price = :price
                        WHERE sku = :sku
                    """),
                    [{"price": potion_price, 
                    "sku": potion['potion_sku']}])
                    
                    # Create catalog entry and add to catalog
                    catalog_entry = {
                                "sku": potion['potion_sku'],
                                "name": potion['potion_sku'],
                                "quantity": potion['quantity'],
                                "price": potion_price,
                                "potion_type": potion['type'],
                            }
                    catalog.append(catalog_entry)

        # Logging
        print("Catalog:")
        for item in catalog:
            print(item)
        print("\n")

        return catalog
