import sqlalchemy
from src import database as db
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from src.api import auth
from src.api import util
import math

router = APIRouter(
    prefix="/audit",
    tags=["audit"],
    dependencies=[Depends(auth.get_api_key)],
)

@router.get("/inventory")
def get_inventory():
    with db.engine.begin() as connection:
        gold = util.get_shop_gold(connection)
        
        num_potions = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(change), 0) as quantity
            FROM potions_ledger
        """)).scalar_one()

        num_ml = connection.execute(sqlalchemy.text("""
            SELECT COALESCE(SUM(change), 0) as quantity
            FROM liquids_ledger
        """)).scalar_one()
    
        return {
            "number_of_potions": num_potions,
            "ml_in_barrels": num_ml, 
            "gold": gold
        }

class Result(BaseModel):
    gold_match: bool
    barrels_match: bool
    potions_match: bool

# Gets called once a day
@router.post("/results")
def post_audit_results(audit_explanation: Result):
    """ """
    print(audit_explanation)

    return "OK"
