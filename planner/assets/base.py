from decimal import Decimal
from typing import Optional
from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel, field_serializer

from planner.util import ZERO
from planner.action import Action

class NotAllowedNegativeBalance(Exception):
    pass

class AssetLog(BaseModel):
    name: str
    balance: Decimal
    category: str

@dataclass
class BaseAsset:
    name: str
    starting_balance: Decimal
    category: str

    def __post_init__(self) -> None:
        self._current_value = float(self.starting_balance)

    def withdraw(self, amount: float, current_date: date, **kwargs):
        real_amount = -1.0 * amount
        self._current_value += real_amount
        return Action(
            amount=real_amount,
            asset_name=self.name,
        )

    def deposit(self, amount: float, current_date: date, **kwargs):
        self._current_value += amount
        return Action(
            amount=amount,
            asset_name=self.name,
        )

    @property
    def log(self) -> AssetLog:
        return AssetLog(
            name=self.name,
            balance=self.current_balance,
            category=self.category,
        )

    @property
    def current_balance(self) -> float:
        return self._current_value
    
    def available_balance(self, current_date: date) -> float:
        return self.current_balance

class BaseAssetInput(BaseModel):
    name: str
    starting_balance: Optional[Decimal] = ZERO
    category: str = "Default"
    
    @field_serializer('starting_balance')
    def serialize_starting_balance(self, starting_balance: Decimal):
        return float(starting_balance)