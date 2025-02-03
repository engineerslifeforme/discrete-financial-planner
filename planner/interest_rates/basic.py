from typing import Literal, Optional
from decimal import Decimal
from dataclasses import dataclass
from datetime import date

from pydantic import BaseModel

from planner.util import future_value, future_interest, interest_of_x

@dataclass
class BaseInterestRate:

    def initialize(self, **kwargs):
        pass

    def daily_rate(self, start_date: date = None) -> float:
        raise NotImplementedError()

    def inflate(self, amount: Decimal, start_date: date = None, days: int = 1) -> float:
        if days > 1:
            print("debug")
        float_amount = float(amount)
        return future_value(float_amount, self.daily_rate(start_date=start_date), days)
    
    def interest(self, amount: Decimal, start_date: date = None, days: int = 1) -> float:
        if days > 1:
            print("debug")
        float_amount = float(amount)
        return future_interest(float_amount, self.daily_rate(start_date=start_date), days)

@dataclass
class BasicInterestRate(BaseInterestRate):
    year_rate_percentage: float
    _daily_interest: Optional[float] = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._daily_interest = interest_of_x(self.year_rate_percentage / 100.0, 365)

    def daily_rate(self, **kwargs) -> float:
        return self._daily_interest

class BaseInterestRateInput(BaseModel):
    interest_type: Literal["DEFAULT"]

    def to_dc_model(self):
        data = self.model_dump()
        data.pop("interest_type", None)
        return self.dc_type(**data)
    
    @property
    def dc_type(self):
        raise NotImplementedError()

class BasicInterestRateInput(BaseInterestRateInput):
    interest_type: Literal["basic"]
    year_rate_percentage: float

    @property
    def dc_type(self):
        return BasicInterestRate