from decimal import Decimal
import math
from datetime import date
from dataclasses import dataclass

from loguru import logger
from pydantic import field_serializer

from planner.transactions.transaction import Transaction, TransactionInput
from planner.period import FrequnecyEnum

def amortorize(period_rate: float, periods: float, amount: float) -> float:
    # https://www.bankrate.com/mortgages/mortgage-calculator/#calculate-mortgage-payment
    term_exponential = math.pow((1 + period_rate), periods)
    numerator = period_rate * term_exponential
    denominator = term_exponential - 1
    return amount * (numerator / denominator)

@dataclass
class Mortgage(Transaction):
    loan_amount: Decimal
    loan_rate: float
    term_months: int

    def __post_init__(self) -> None:
        super().__post_init__()
        self._complete = False
        self._payment = amortorize(
            self.loan_rate_month, 
            float(self.term_months),
            float(self.loan_amount),
        )

    @property
    def loan_rate_month(self):
        return self.loan_rate / 100.0 / 12.0
    
    @property
    def payment_interest(self):
        return float(abs(self.destination.current_balance)) * self.loan_rate_month
    
    def execute(self, days: int, current_date: date) -> list:
        actions = []
        current_payment_interest = self.payment_interest
        remaining_balance = abs(self.destination.current_balance)
        payment_principal = self._payment - current_payment_interest        
        closeout = False
        if payment_principal > remaining_balance:
            # Closeout / Last Payment
            principal_portion = remaining_balance
            closeout = True
        else:
            principal_portion = payment_principal
        action = self.source.withdraw(principal_portion, current_date)
        action.description = f"{self.name} Principal Payment"
        actions.append(action)
        
        action = self.source.withdraw(current_payment_interest, current_date)
        action.description = f"{self.name} Interest Payment"
        action.fed_tax_deductible = True
        actions.append(action)
        
        action = self.destination.deposit(principal_portion, current_date)
        action.description=f"{self.name} Principal Payment"
        actions.append(action)
        if closeout:
            logger.debug(f"Mortgage: {self.name} complete on {current_date}")
            self._complete = True
        for action in actions:
            action.priority = self.priority
            action.category = self.category
        return actions
    
    def is_valid(self, *args, **kwargs) -> bool:
        result = super().is_valid(*args, **kwargs)
        return result and not self._complete
    
class MortgageInput(TransactionInput):
    loan_amount: Decimal
    loan_rate: float
    term_months: int
    frequency: FrequnecyEnum = FrequnecyEnum.monthly

    def model_post_init(self, __context) -> None:
        assert(self.frequency == FrequnecyEnum.monthly), "Mortgages must have a montly frequency"
        assert(self.source is not None)
        assert(self.destination is not None)

    @property
    def _destination_class(self):
        return Mortgage    
    
    @field_serializer('loan_amount')
    def serialize_loan_amount(self, loan_amount: Decimal):
        return float(loan_amount)