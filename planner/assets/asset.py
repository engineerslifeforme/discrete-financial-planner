from typing import Literal

from planner.assets.base import BaseAsset

class NotAllowedNegativeBalance(Exception):
    pass

class Asset(BaseAsset):
    type: Literal["asset"]
    
    def withdraw(self, amount: float):
        super().withdraw(amount)
        if self.current_balance < 0.0:
            raise NotAllowedNegativeBalance(f"Withdrawal of {amount} from {self.name} resulted in a negative balance of ${self.current_balance}")