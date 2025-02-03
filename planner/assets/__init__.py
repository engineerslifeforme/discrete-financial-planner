from typing import Union

from planner.assets.asset import Asset, NotAllowedNegativeBalance, AssetInput
from planner.assets.debt import Debt, DebtInput
from planner.assets.base import AssetLog
from planner.assets.retirement import Retirement, RetirementInput

asset_input_options = Union[AssetInput, DebtInput, RetirementInput]
asset_options = Union[Asset, Debt, Retirement]