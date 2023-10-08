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
        data = util.get_shop_data(connection)
    
        return {
            "number_of_potions": data.num_red_potions + data.num_green_potions + data.num_blue_potions,
            "ml_in_barrels": data.num_red_ml + data.num_green_ml + data.num_blue_ml, 
            "gold": data.gold
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
