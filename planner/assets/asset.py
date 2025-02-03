from typing import Literal
from dataclasses import dataclass
from datetime import date

from planner.assets.base import BaseAssetInput, BaseAsset, NotAllowedNegativeBalance

@dataclass
class Asset(BaseAsset):
    
    def withdraw(self, amount: float, current_date: date, **kwargs):
        if amount > self.current_balance:
            raise NotAllowedNegativeBalance(f"Withdrawal of {amount} on {current_date} from {self.name} resulted in a negative balance of ${self.current_balance}")
        action = super().withdraw(amount, current_date, **kwargs)
        return action

class AssetInput(BaseAssetInput):
    type: Literal["asset"]

    @property
    def _destination_class(self):
        return Asset

    def to_dc_model(self):
        data = self.model_dump()
        data.pop("type", None)
        return self._destination_class(**data)