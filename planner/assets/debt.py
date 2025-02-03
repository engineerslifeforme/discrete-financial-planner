from typing import Literal
from dataclasses import dataclass

from planner.assets.base import BaseAssetInput, BaseAsset

@dataclass
class Debt(BaseAsset):
    pass

class DebtInput(BaseAssetInput):
    type: Literal["debt"]

    def to_dc_model(self):
        data = self.model_dump()
        data.pop("type", None)
        return Debt(**data)