from dataclasses import dataclass

from planner.transactions.transaction import Transaction, TransactionInput
from planner.assets import NotAllowedNegativeBalance

@dataclass
class MaintainBalance(Transaction):
    maintain_balance: float
    error_on_insufficient_source: bool

    def _get_amount(self, *args) -> float:
        transfer_amount = self.maintain_balance - self.destination.current_balance
        if transfer_amount > self.source.current_balance:
            transfer_amount = self.source.current_balance
        return transfer_amount
    
    def execute(self, *args, **kwargs):
        try:
            return super().execute(*args, **kwargs)
        except NotAllowedNegativeBalance:
            if self.error_on_insufficient_source:
                raise
            else:
                return []

class MaintainBalanceInput(TransactionInput):
    maintain_balance: float
    error_on_insufficient_source: bool = False

    def model_post_init(self, __context) -> None:
        assert(self.destination is not None), "Maintain balance must have a destination"
        assert(self.source is not None), "Maintain balance must have a source"

    @property
    def _destination_class(self):
        return MaintainBalance