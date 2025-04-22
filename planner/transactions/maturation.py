from dataclasses import dataclass
from datetime import date

from planner.transactions.transaction import Transaction, TransactionInput
from planner.period import FrequnecyEnum

@dataclass
class Maturation(Transaction):
    maturation: bool

    def __post_init__(self):
        super().__post_init__()
        self._deposit_kwargs["contribution"] = False

    def _get_amount(self, days: int, current_date: date) -> float:
        balance = self.destination.current_balance
        if balance > 0.0:
            amount = self.interest_rate.interest(balance, days=1, start_date=current_date)
            return amount
        return 0.0

class MaturationInput(TransactionInput):
    frequency: FrequnecyEnum = FrequnecyEnum.daily
    maturation: bool

    def model_post_init(self, __context) -> None:
        assert(self.frequency == FrequnecyEnum.daily), "Maturation must have daily frequency"
        assert(self.maturation), "Maturation must be true if set, otherwise remove"
        assert(self.interest_rate is not None), "Maturation must have an interest rate"
        assert(self.destination is not None), "Maturation must have a destination"
        assert(self.source is None), "Maturation cannot have a source"

    @property
    def _destination_class(self):
        return Maturation