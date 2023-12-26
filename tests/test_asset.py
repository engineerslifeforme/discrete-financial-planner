from decimal import Decimal

import yaml
import pytest

from planner import Asset
from planner.interest_rate import InterestRate
from planner.common import ZERO

@pytest.fixture
def default_asset():
    return Asset(name="default")

EXAMPLE_BALANCE = Decimal("100.00")
EXAMPLE_RATE = 7.0

@pytest.fixture
def example_asset():
    rate_name = "default"
    interest_rate = InterestRate(name=rate_name,rate=EXAMPLE_RATE)
    asset = Asset(
        name="default",
        balance=EXAMPLE_BALANCE,
        interest_rate=rate_name,
    )
    asset.get_interest_rate({
        rate_name: interest_rate
    })
    return asset

def test_asset():
    asset = Asset(**yaml.safe_load("name: An Asset"))
    assert(asset.name == "An Asset")
    assert(asset.balance == ZERO)
    
    asset = Asset(**yaml.safe_load("""name: An Asset2
balance: 100.00"""))
    assert(asset.name == "An Asset2")
    assert(asset.balance == Decimal("100.00"))

def test_mature(example_asset):
    assert(example_asset.balance == EXAMPLE_BALANCE)
    example_asset.mature()
    assert(example_asset.f_balance == float(EXAMPLE_BALANCE) * (1.0 + ((EXAMPLE_RATE / 100.0) / 365.0)))