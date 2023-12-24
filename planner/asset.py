from decimal import Decimal

from pydantic import BaseModel

from planner.common import ZERO

class Asset(BaseModel):
    name: str
    balance: Decimal = ZERO