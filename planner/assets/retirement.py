from decimal import Decimal
from dataclasses import dataclass
from datetime import date
from typing import Optional

from pydantic import field_serializer

from planner.assets.asset import Asset, AssetInput
from planner.assets.base import NotAllowedNegativeBalance
from planner.action import Action

class NotAllowedEarlyWithdrawal(Exception):
    pass

@dataclass
class Retirement(Asset):
    contributions: Decimal
    contributions_available_date: Optional[date]
    interest_available_date: Optional[date]

    def __post_init__(self) -> None:
        self._current_contributions = float(self.contributions)
        self._current_interest = float(self.starting_balance - self._current_contributions)

    def deposit(self, amount: float, current_date: date, contribution: bool = True):
        if contribution:
            self._current_contributions += amount
        else:
            self._current_interest += amount
        return Action(
            amount=amount,
            asset_name=self.name,
        )
    
    def withdraw(self, amount: float, current_date: date, contribution: bool = False):
        real_amount = -1.0 * amount
        contribution_withdrawal = 0.0
        interest_withdrawal = 0.0

        if contribution:
            contribution_withdrawal = real_amount
        else:       
            if self.interest_available(current_date):
                if amount <= self._current_interest:
                    interest_withdrawal = real_amount
                else:
                    contribution_withdrawal = real_amount + self._current_interest
                    interest_withdrawal = -1.0 * self._current_interest
        
        if contribution_withdrawal != 0.0 and self.contributions_available_date is not None:
            if current_date < self.contributions_available_date:
                raise NotAllowedEarlyWithdrawal(f"Contributions not avialable from {self.name} on {current_date}, available on {self.contributions_available_date}")
        if interest_withdrawal != 0.0 and self.interest_available_date is not None:
            if current_date < self.contributions_available_date:
                raise NotAllowedEarlyWithdrawal(f"Interest not avialable from {self.name} on {current_date}, available on {self.interest_available_date}")
        if abs(contribution_withdrawal) > self._current_contributions:
            raise NotAllowedNegativeBalance(f"Withdrawal of {amount} on {current_date} from {self.name} would result in a negative contribution balance")
        
        self._current_contributions += contribution_withdrawal
        self._current_interest += interest_withdrawal
        return Action(
            amount=real_amount,
            asset_name=self.name,
        )
    
    def _contributions_available(self, current_date: date) -> bool:
        contributions_available = False
        if self.contributions_available_date is None:
            contributions_available = True
        else:
            if current_date >= self.contributions_available_date:
                contributions_available = True
        return contributions_available
    
    def _interest_available(self, current_date: date) -> bool:
        interest_available = False
        if self.interest_available_date is None:
            interest_available = True
        else:
            if current_date >= self.interest_available_date:
                interest_available = True
        return interest_available
    
    @property
    def current_balance(self) -> float:
        return self._current_contributions + self._current_interest

    def available_balance(self, current_date: date) -> float:
        available_balance = 0.0
        if self.contributions_available_date is None:
            available_balance += self._current_contributions
        else:
            if current_date >= self.contributions_available_date:
                available_balance += self._current_contributions
        if self.interest_available_date is None:
            available_balance += self._current_interest
        else:
            if current_date >= self.interest_available_date:
                available_balance += self._current_interest
        return available_balance 

class RetirementInput(AssetInput):
    contributions: Decimal
    contributions_available_date: Optional[date] = None
    interest_available_date: Optional[date] = None

    @property
    def _destination_class(self):
        return Retirement
    
    @field_serializer('contributions')
    def serialize_contributions(self, contributions: Decimal):
        return float(contributions)

