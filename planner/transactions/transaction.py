from decimal import Decimal
from typing import Optional, Union
from datetime import date
from dataclasses import dataclass

from pydantic import field_serializer

from planner.util import ZERO
from planner.interest_rates import interest_rate_options
from planner.assets import asset_options, NotAllowedNegativeBalance
from planner.period import FrequencyModel, FrequencyModelInput, FrequnecyEnum
from planner.action import Action

@dataclass
class Transaction(FrequencyModel):
    name: str
    base_amount: Decimal 
    source: Optional[Union[asset_options, str]]
    destination: Optional[Union[asset_options, str]]
    interest_rate: Optional[Union[interest_rate_options, str]]
    priority: int
    category: Optional[str]
    contribution_only: bool
    full_amount_not_required: bool
    fed_taxable: bool
    fed_tax_payment: bool
    fed_tax_deductible: bool
    donation_percentage: Optional[float]

    def __post_init__(self):
        super().__post_init__()
        self.set_base_amount(self.base_amount)
        if self.category is None:
            self.category = self.name
        self._withdrawal_kwargs = {
            "contribution": self.contribution_only,
        }
        self._deposit_kwargs = {}

    def set_base_amount(self, amount: Decimal):
        self.base_amount = amount
        self._f_base_amount = float(self.base_amount)

    def _get_amount(self, days: int, current_date: date) -> float:
        if self.interest_rate is not None:
            return self.interest_rate.inflate(self.base_amount, start_date=current_date, days=days)
        else:
            return self._f_base_amount
        
    def load_assets(self, assets: dict):
        if self.source is not None:
            self.source = assets[self.source]
        if self.destination is not None:
            self.destination = assets[self.destination]

    def _fill_action(self, action: Action) -> Action:
        action.description=self.name
        action.priority=self.priority
        action.category = self.category
        action.fed_taxable = self.fed_taxable
        action.fed_tax_payment = self.fed_tax_payment
        action.fed_tax_deductible = self.fed_tax_deductible
        return action
        
    def execute(self, days: int, current_date: date) -> list:
        actions = []
        amount = self._get_amount(days, current_date)
        if amount <= 0.0:
            return actions
        if self.source is not None:
            available_balance = self.source.available_balance(current_date)
            if amount > available_balance and self.full_amount_not_required:
                amount = available_balance
            action = self.source.withdraw(amount, current_date, **self._withdrawal_kwargs)
            action = self._fill_action(action)
            actions.append(action)
        if self.destination is not None:
            action = self.destination.deposit(amount, current_date, **self._deposit_kwargs)
            action = self._fill_action(action)
            actions.append(action)
        if self.donation_percentage is not None:
            donation_amount = (self.donation_percentage / 100.0) * amount
            action = self.destination.withdraw(donation_amount, current_date)
            action.description=self.name + " Donation"
            action.priority=self.priority
            action.category = "Donation"
            action.fed_tax_deductible = True
            actions.append(action)
        return actions
    
    def load_interest_rate(self, interest_rates: dict):
        if self.interest_rate is not None:
            self.interest_rate = interest_rates[self.interest_rate]

class TransactionInput(FrequencyModelInput):
    name: str
    base_amount: Decimal = ZERO
    source: Optional[str] = None
    destination: Optional[str] = None
    interest_rate: Optional[str] = None
    priority: int = 100
    category: Optional[str] = None
    contribution_only: bool = False
    full_amount_not_required: bool = False
    fed_taxable: bool = False
    fed_tax_payment: bool = False
    fed_tax_deductible: bool = False
    donation_percentage: Optional[float] = None

    @property
    def _destination_class(self):
        return Transaction

    @field_serializer('base_amount')
    def serialize_base_amount(self, base_amount: Decimal):
        return float(base_amount)

    def to_dc_model(self):
        data = self.model_dump()
        data.pop("source", None)
        data.pop("destination", None)
        data.pop("interest_rate", None)
        if self.frequency == FrequnecyEnum.biweekly:
            data["frequency"] = FrequnecyEnum.weekly
            data["every_x_periods"] = 2
        return self._destination_class(
            source=self.source,
            destination=self.destination,
            interest_rate=self.interest_rate,
            **data,
        )