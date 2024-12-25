from typing import Literal, Optional
from decimal import Decimal
import math

from pydantic import BaseModel

from planner.util import future_value

class BasicInterestRate(BaseModel):
    interest_type: Literal["basic"]
    year_rate_percentage: float

    @property
    def daily_rate(self) -> float:
        return self.year_rate_percentage / 365.0

    def inflate(self, amount: Decimal, days: int = 1) -> float:
        float_amount = float(amount)
        return future_value(float_amount, self.daily_rate, days)