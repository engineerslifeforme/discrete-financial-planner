from planner.transactions.transaction import Transaction, TransactionInput
from dataclasses import dataclass

@dataclass
class DebtPayment(Transaction):
    only_if_destination_balance_negative: bool

    def _get_amount(self, *args, **kwargs) -> float:
        amount = super()._get_amount(*args, **kwargs)
        if self.only_if_destination_balance_negative:
            destination_balance = self.destination.current_balance
            if destination_balance >= 0.0:
                amount = 0.0
            else:
                abs_destination_balance = abs(destination_balance)
                if amount > abs_destination_balance:
                    amount = abs_destination_balance
        return amount
    
class DebtPaymentInput(TransactionInput):
    only_if_destination_balance_negative: bool

    def model_post_init(self, __context) -> None:
        assert(self.source is not None)
        assert(self.destination is not None)

    @property
    def _destination_class(self):
        return DebtPayment