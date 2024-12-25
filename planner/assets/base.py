from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, field_serializer

from planner.util import ZERO

class AssetLog(BaseModel):
    name: str
    balance: Decimal

class BaseAsset(BaseModel):
    name: str
    starting_balance: Optional[Decimal] = ZERO

    def model_post_init(self, __context) -> None:
        self._current_value = float(self.starting_balance)

    def withdraw(self, amount: float):
        self._current_value -= amount

    def deposit(self, amount: float):
        self._current_value += amount

    @property
    def log(self) -> AssetLog:
        return AssetLog(
            name=self.name,
            balance=self._current_value,
        )

    @property
    def current_balance(self) -> float:
        return self._current_value
    
    @field_serializer('starting_balance')
    def serialize_starting_balance(self, starting_balance: Decimal):
        return float(starting_balance)