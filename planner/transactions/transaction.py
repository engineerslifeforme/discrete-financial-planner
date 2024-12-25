from decimal import Decimal
from typing import Optional, Union

from pydantic import field_serializer, BaseModel

from planner.util import ZERO
from planner.interest_rates.basic import BasicInterestRate
from planner.period import (
    DailyFrequency,
    WeeklyFrequency,
    BiweeklyFrequency,
    MonthlyFrequency,
    YearlyFrequency,
)
from planner.action import Action

class Transaction(BaseModel):
    name: str
    base_amount: Decimal = ZERO
    source_name: Optional[str] = None
    destination_name: Optional[str] = None
    interest_rate: Optional[Union[BasicInterestRate, str]] = None
    priority: int = 100
    empty_source: bool = False

    @field_serializer('base_amount')
    def serialize_base_amount(self, base_amount: Decimal):
        return float(base_amount)

    def model_post_init(self, __context) -> None:
        self._f_base_amount = float(self.base_amount)

    def load_interest_rate(self, interest_rates: dict):
        if type(self.interest_rate) == str:
            self.interest_rate = interest_rates[self.interest_rate]

    def _get_amount(self, days: int) -> float:
        if self.interest_rate is not None:
            return self.interest_rate.inflate(self.base_amount, days)
        else:
            return self._f_base_amount

    def get_actions(self, days: int) -> list:
        return [Action(
            amount=self._get_amount(days),
            description=self.name,
            source_name=self.source_name,
            destination_name=self.destination_name,
            priority=self.priority,
            empty_source=self.empty_source,
        )]
    
class DailyTransaction(Transaction, DailyFrequency):
    pass

class WeeklyTransaction(Transaction, WeeklyFrequency):
    pass

class BiweeklyTransaction(Transaction, BiweeklyFrequency):
    pass

class MonthlyTransaction(Transaction, MonthlyFrequency):
    pass

class YearlyTransaction(Transaction, YearlyFrequency):
    pass