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
        potions_catalog = connection.execute(sqlalchemy.text("SELECT sku, type, price FROM potions"))

        # Add each potion type to the cart, if available
        for sku, type, price in potions_catalog:
            quantity = connection.execute(sqlalchemy.text("""
                SELECT SUM(change)
                FROM potions_ledger
                WHERE potion_sku = :sku"""),
            [{"sku": sku}]).scalar_one()

            if quantity > 0:
                catalog_entry = {
                            "sku": sku,
                            "name": sku,
                            "quantity": quantity,
                            "price": price,
                            "potion_type": type,
                        }
                catalog.append(catalog_entry)

        # Logging
        print("Catalog:")
        for item in catalog:
            print(item)
        print("\n")

        return catalog
