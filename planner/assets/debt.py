from typing import Literal

from planner.assets.base import BaseAsset

class Debt(BaseAsset):
    type: Literal["debt"]