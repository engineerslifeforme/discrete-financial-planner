from decimal import Decimal

import yaml

from planner import Asset
from planner.common import ZERO

def test_asset():
    asset = Asset(**yaml.safe_load("name: An Asset"))
    assert(asset.name == "An Asset")
    assert(asset.balance == ZERO)
    
    asset = Asset(**yaml.safe_load("""name: An Asset2
balance: 100.00"""))
    assert(asset.name == "An Asset2")
    assert(asset.balance == Decimal("100.00"))