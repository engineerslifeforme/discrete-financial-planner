import pytest

from planner.assets import Asset, NotAllowedNegativeBalance

def test_withdraw():
    starting_balance = 1.00
    asset = Asset(
        type="asset",
        name="a",
        starting_balance = starting_balance,
    )
    assert(asset.log.balance == starting_balance)
    asset.withdraw(starting_balance)
    assert(asset.log.balance == 0.00)
    with pytest.raises(NotAllowedNegativeBalance):
        asset.withdraw(starting_balance)

    asset = Asset(
        type="asset",
        name="a",
        starting_balance = starting_balance,
    )
    asset.deposit(starting_balance)
    assert(asset.log.balance == starting_balance * 2)