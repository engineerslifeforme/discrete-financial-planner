from planner.transactions.transaction import Transaction, TransactionInput
from dataclasses import dataclass

@dataclass
class Sweep(Transaction):
    sweep_greater_than: float

    # TODO: consider inflation of sweep balance

    def _get_amount(self, *args, **kwargs) -> float:
        amount = 0.0
        if self.source.current_balance > self.sweep_greater_than:
            amount = self.source.current_balance - self.sweep_greater_than
        return amount
    
class SweepInput(TransactionInput):
    sweep_greater_than: float

    def model_post_init(self, __context) -> None:
        assert(self.source is not None)

    @property
    def _destination_class(self):
        return Sweep